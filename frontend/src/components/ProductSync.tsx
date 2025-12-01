import { useState } from 'react'
import toast from 'react-hot-toast'
import { mappingApi, shopwareApi } from '../utils/api'
import type { FieldMapping, SyncResult } from '../types'

interface ProductSyncProps {
  mapping: FieldMapping[]
}

function ProductSync({ mapping }: ProductSyncProps) {
  const [articleIds, setArticleIds] = useState<string>('')
  const [syncMode, setSyncMode] = useState<'create' | 'update' | 'upsert'>('upsert')
  const [syncing, setSyncing] = useState(false)
  const [results, setResults] = useState<SyncResult[]>([])
  const [showResults, setShowResults] = useState(false)
  const [syncProgress, setSyncProgress] = useState<{ current: number; total: number } | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)

  const handleSync = async () => {
    if (mapping.length === 0) {
      toast.error('Bitte definieren Sie zuerst Field-Mappings')
      return
    }

    if (!articleIds.trim()) {
      toast.error('Bitte geben Sie Artikel-IDs ein')
      return
    }

    // Parse article IDs (comma or space separated)
    // Keep as strings so backend can decide if it's an article number or ID
    const ids = articleIds
      .split(/[,\s]+/)
      .map((id) => id.trim())
      .filter((id) => id !== '')

    if (ids.length === 0) {
      toast.error('Keine gültigen Artikel-IDs gefunden')
      return
    }

    setSyncing(true)
    setResults([])
    setShowResults(true)
    setSyncProgress(null)

    try {
      const syncResults = await mappingApi.syncProducts(ids, mapping, syncMode)

      setResults(syncResults.results)

      if (syncResults.successful === syncResults.total) {
        toast.success(`Alle ${syncResults.total} Artikel erfolgreich synchronisiert`)
      } else {
        toast.error(
          `${syncResults.successful} von ${syncResults.total} Artikeln synchronisiert`
        )
      }
    } catch (error: any) {
      toast.error(`Fehler beim Synchronisieren: ${error.message}`)
      console.error(error)
    }

    setSyncing(false)
  }

  const handleAbort = () => {
    if (abortController) {
      abortController.abort()
      setAbortController(null)
      setSyncing(false)
      setSyncProgress(null)
      toast.error('Synchronisation abgebrochen')
    }
  }

  const handleSyncAll = async () => {
    if (mapping.length === 0) {
      toast.error('Bitte definieren Sie zuerst Field-Mappings')
      return
    }

    if (
      !window.confirm(
        'Möchten Sie wirklich ALLE Artikel aus Shopware 5 synchronisieren? Dies kann lange dauern.'
      )
    ) {
      return
    }

    const controller = new AbortController()
    setAbortController(controller)
    setSyncing(true)
    setResults([])
    setShowResults(true)
    setSyncProgress(null)

    try {
      // First, get just one article to check the total count
      const firstPage = await shopwareApi.getArticles(1, 0)
      const totalCount = firstPage.total

      if (totalCount === 0) {
        toast.error('Keine Artikel in Shopware 5 gefunden')
        setSyncing(false)
        return
      }

      setSyncProgress({ current: 0, total: totalCount })
      toast(`Lade ${totalCount} Artikel aus Shopware 5...`)

      // Fetch all articles with pagination (500 per page for better performance)
      const allArticleIds: number[] = []
      const pageSize = 500
      const totalPages = Math.ceil(totalCount / pageSize)

      for (let page = 0; page < totalPages; page++) {
        const offset = page * pageSize
        const articlesData = await shopwareApi.getArticles(pageSize, offset)
        const pageIds = articlesData.data.map((article: any) => article.id)
        allArticleIds.push(...pageIds)

        toast(`Geladen: ${allArticleIds.length} / ${totalCount} Artikel`, { duration: 1000 })
      }

      toast(`Synchronisiere ${allArticleIds.length} Artikel...`)

      // Process in batches to show progress
      const batchSize = 50
      const allResults: SyncResult[] = []
      const totalArticles = allArticleIds.length
      let processedCount = 0

      for (let i = 0; i < allArticleIds.length; i += batchSize) {
        // Check if aborted
        if (controller.signal.aborted) {
          toast.error('Synchronisation abgebrochen')
          break
        }

        const batch = allArticleIds.slice(i, i + batchSize)

        // Update progress
        const batchStart = i + 1
        const batchEnd = Math.min(i + batchSize, totalArticles)
        setSyncProgress({ current: batchStart, total: totalArticles })
        toast(`Verarbeite Artikel ${batchStart}-${batchEnd} von ${totalArticles}...`, { duration: 2000 })

        // Sync this batch
        try {
          const batchResults = await mappingApi.syncProducts(batch, mapping, syncMode)
          allResults.push(...batchResults.results)
          processedCount += batch.length

          // Update results and progress in real-time
          setResults([...allResults])
          setSyncProgress({ current: processedCount, total: totalArticles })

          // Show intermediate progress
          const successCount = allResults.filter(r => r.success).length
          const failCount = allResults.filter(r => !r.success).length
          console.log(`Progress: ${processedCount}/${totalArticles} | Erfolg: ${successCount} | Fehler: ${failCount}`)
        } catch (error: any) {
          if (controller.signal.aborted) {
            break
          }
          throw error
        }
      }

      // Final summary
      const finalSuccessCount = allResults.filter(r => r.success).length
      const finalFailCount = allResults.filter(r => !r.success).length

      setSyncProgress(null)

      if (finalSuccessCount === totalArticles) {
        toast.success(`Alle ${totalArticles} Artikel erfolgreich synchronisiert`)
      } else {
        toast.error(
          `${finalSuccessCount} von ${totalArticles} Artikeln synchronisiert (${finalFailCount} Fehler)`
        )
      }
    } catch (error: any) {
      if (!controller.signal.aborted) {
        toast.error(`Fehler beim Synchronisieren: ${error.message}`)
        console.error(error)
      }
      setSyncProgress(null)
    }

    setAbortController(null)
    setSyncing(false)
  }

  return (
    <div className="card">
      <h2>Produkt-Synchronisation</h2>

      <div className="sync-controls">
        <div style={{ flex: 1 }}>
          <label htmlFor="articleIds" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Shopware 5 Artikel-IDs (komma- oder leerzeichengetrennt):
          </label>
          <input
            id="articleIds"
            type="text"
            className="input"
            placeholder="z.B. 1, 2, 3 oder SW12836, 6641"
            value={articleIds}
            onChange={(e) => setArticleIds(e.target.value)}
            style={{ width: '100%' }}
            disabled={syncing}
          />
          <small style={{ color: '#666', marginTop: '0.25rem', display: 'block' }}>
            Hinweis: Geben Sie Shopware Artikel-IDs ein (nicht Shopify Produkt-IDs).
            Diese werden nach Shopify exportiert.
          </small>
        </div>

        <div>
          <label htmlFor="syncMode" style={{ display: 'block', marginBottom: '0.5rem' }}>
            Sync-Modus:
          </label>
          <select
            id="syncMode"
            className="select"
            value={syncMode}
            onChange={(e) => setSyncMode(e.target.value as any)}
            disabled={syncing}
          >
            <option value="upsert">Upsert (erstellen/aktualisieren)</option>
            <option value="create">Nur erstellen</option>
            <option value="update">Nur aktualisieren</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: 'auto' }}>
          <button
            className="button button-success"
            onClick={handleSync}
            disabled={syncing || !articleIds.trim()}
          >
            {syncing ? (
              <>
                <span className="loading" style={{ marginRight: '0.5rem' }} />
                Synchronisiere...
              </>
            ) : (
              'Ausgewählte synchronisieren'
            )}
          </button>

          <button
            className="button button-secondary"
            onClick={handleSyncAll}
            disabled={syncing}
          >
            Alle Artikel synchronisieren
          </button>

          {syncing && abortController && (
            <button
              className="button button-danger"
              onClick={handleAbort}
              style={{ marginTop: '0.5rem' }}
            >
              ⚠️ Synchronisation abbrechen
            </button>
          )}
        </div>
      </div>

      {syncProgress && (
        <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <strong>Synchronisationsfortschritt</strong>
            <span>{syncProgress.current} / {syncProgress.total} Artikel ({Math.round((syncProgress.current / syncProgress.total) * 100)}%)</span>
          </div>
          <div style={{ width: '100%', height: '24px', backgroundColor: '#e5e7eb', borderRadius: '12px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${(syncProgress.current / syncProgress.total) * 100}%`,
                height: '100%',
                backgroundColor: '#3b82f6',
                transition: 'width 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '12px',
                fontWeight: 'bold'
              }}
            >
              {Math.round((syncProgress.current / syncProgress.total) * 100)}%
            </div>
          </div>
        </div>
      )}

      {showResults && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Sync-Ergebnisse</h3>

          {results.length === 0 && syncing && (
            <p style={{ color: '#666', fontStyle: 'italic' }}>
              Synchronisation läuft...
            </p>
          )}

          {results.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <div style={{ marginBottom: '1rem' }}>
                <span className="status-badge status-success">
                  Erfolgreich: {results.filter((r) => r.success).length}
                </span>{' '}
                <span className="status-badge status-error">
                  Fehlgeschlagen: {results.filter((r) => !r.success).length}
                </span>
              </div>

              <div
                style={{
                  maxHeight: '400px',
                  overflowY: 'auto',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                }}
              >
                {results.map((result, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '1rem',
                      borderBottom: '1px solid #eee',
                      backgroundColor: result.success ? '#f8f9fa' : '#fff3f3',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <div>
                        <strong>Artikel ID:</strong> {result.sw5_article_id}
                      </div>
                      <div>
                        <span
                          className={`status-badge ${
                            result.success ? 'status-success' : 'status-error'
                          }`}
                        >
                          {result.status}
                        </span>
                      </div>
                    </div>

                    {result.shopify_product_id && (
                      <div style={{ marginTop: '0.5rem' }}>
                        <strong>Shopify Product ID:</strong> {result.shopify_product_id}
                      </div>
                    )}

                    {result.error && (
                      <div style={{ marginTop: '0.5rem', color: '#dc3545' }}>
                        <strong>Fehler:</strong> {result.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ProductSync
