import { useState, useEffect } from 'react'
import { Toaster, toast } from 'react-hot-toast'
import ConnectionStatus from './components/ConnectionStatus'
import FieldMapper from './components/FieldMapper'
import ProductSync from './components/ProductSync'
import {
  loadMapping,
  saveMapping,
  downloadMappingsAsJson,
  uploadMappingsFromJson,
  migrateOldMappings
} from './utils/storage'
import type { FieldMapping, EntityType } from './types'

function App() {
  const [activeEntityType, setActiveEntityType] = useState<EntityType>('articles')
  const [mapping, setMapping] = useState<FieldMapping[]>([])

  // Migrate old mappings and load current entity mapping
  useEffect(() => {
    migrateOldMappings()
    const savedMapping = loadMapping(activeEntityType)
    setMapping(savedMapping)
  }, [activeEntityType])

  const handleMappingChange = (newMapping: FieldMapping[]) => {
    setMapping(newMapping)
    saveMapping(activeEntityType, newMapping)
  }

  const handleExportMappings = () => {
    try {
      downloadMappingsAsJson()
      toast.success('Mappings erfolgreich exportiert!')
    } catch (error) {
      toast.error(`Export fehlgeschlagen: ${error}`)
    }
  }

  const handleImportMappings = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      try {
        await uploadMappingsFromJson(file)
        // Reload current entity mapping
        const updatedMapping = loadMapping(activeEntityType)
        setMapping(updatedMapping)
        toast.success('Mappings erfolgreich importiert!')
      } catch (error) {
        toast.error(`Import fehlgeschlagen: ${error}`)
      }
      // Clear file input
      e.target.value = ''
    }
  }

  return (
    <>
      <Toaster position="top-right" />

      <div className="header">
        <div className="container">
          <h1>SW5 to Shopify Import Tool</h1>
          <p>Artikel, Bestellungen und Kunden aus Shopware 5 zu Shopify migrieren</p>
        </div>
      </div>

      <div className="container">
        <ConnectionStatus />

        {/* Tab Navigation */}
        <div className="tabs">
          <button
            className={`tab ${activeEntityType === 'articles' ? 'active' : ''}`}
            onClick={() => setActiveEntityType('articles')}
          >
            Artikel
          </button>
          <button
            className={`tab ${activeEntityType === 'orders' ? 'active' : ''}`}
            onClick={() => setActiveEntityType('orders')}
          >
            Bestellungen
          </button>
          <button
            className={`tab ${activeEntityType === 'customers' ? 'active' : ''}`}
            onClick={() => setActiveEntityType('customers')}
          >
            Kunden
          </button>

          {/* Import/Export Buttons */}
          <div className="tab-actions">
            <button
              className="button button-secondary"
              onClick={handleExportMappings}
              title="Alle Mappings als JSON exportieren"
            >
              Export
            </button>
            <label className="button button-secondary" title="Mappings aus JSON importieren">
              Import
              <input
                type="file"
                accept=".json"
                onChange={handleImportMappings}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        </div>

        <FieldMapper
          entityType={activeEntityType}
          mapping={mapping}
          onMappingChange={handleMappingChange}
        />

        <ProductSync
          entityType={activeEntityType}
          mapping={mapping}
        />
      </div>
    </>
  )
}

export default App
