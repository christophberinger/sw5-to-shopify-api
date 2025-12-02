import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { entityApi, shopwareApi, shopifyApi } from '../utils/api'
import type { Field, FieldMapping, TransformationRule, EntityType } from '../types'
import { ENTITY_CONFIGS } from '../types'
import TransformationEditor from './TransformationEditor'

interface FieldMapperProps {
  entityType: EntityType
  mapping: FieldMapping[]
  onMappingChange: (mapping: FieldMapping[]) => void
}

function FieldMapper({ entityType, mapping, onMappingChange }: FieldMapperProps) {
  const config = ENTITY_CONFIGS[entityType]
  const [sw5Fields, setSw5Fields] = useState<Field[]>([])
  const [shopifyFields, setShopifyFields] = useState<Field[]>([])
  const [selectedSw5Field, setSelectedSw5Field] = useState<string | null>(null)
  const [selectedShopifyField, setSelectedShopifyField] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [sw5SearchTerm, setSw5SearchTerm] = useState('')
  const [shopifySearchTerm, setShopifySearchTerm] = useState('')
  const [articleNumber, setArticleNumber] = useState('')
  const [productIdentifier, setProductIdentifier] = useState('')
  const [editingMappingIndex, setEditingMappingIndex] = useState<number | null>(null)

  useEffect(() => {
    loadFields()
  }, [entityType])

  const loadFields = async (identifier?: string) => {
    setLoading(true)

    try {
      const [sw5FieldsData, shopifyFieldsData] = await Promise.all([
        entityApi.getFields(entityType, 'shopware', identifier),
        entityApi.getFields(entityType, 'shopify', identifier),
      ])

      setSw5Fields(sw5FieldsData)
      setShopifyFields(shopifyFieldsData)

      let successMsg = 'Felder erfolgreich geladen'
      if (identifier) {
        successMsg = `Felder für ${config.sw5Label} ${identifier} geladen`
      }
      toast.success(successMsg)
    } catch (error: any) {
      // Show detailed error message from backend
      const errorMsg = error.response?.data?.detail || error.message || 'Fehler beim Laden der Felder'

      if (error.response?.status === 404 && identifier) {
        toast.error(`${config.sw5Label} "${identifier}" nicht gefunden. Bitte prüfen Sie die ID oder laden Sie ohne ID.`)
      } else {
        toast.error(errorMsg)
      }

      console.error(error)

      // If not found, still try to load default fields
      if (error.response?.status === 404 && identifier) {
        try {
          const [sw5FieldsData, shopifyFieldsData] = await Promise.all([
            entityApi.getFields(entityType, 'shopware'),
            entityApi.getFields(entityType, 'shopify'),
          ])
          setSw5Fields(sw5FieldsData)
          setShopifyFields(shopifyFieldsData)
          toast.success('Standard-Felder geladen')
        } catch (fallbackError) {
          console.error('Fallback error:', fallbackError)
        }
      }
    }

    setLoading(false)
  }

  const handleLoadByIdentifiers = () => {
    const identifier = articleNumber.trim() || productIdentifier.trim() || undefined
    loadFields(identifier)
  }

  const addMapping = () => {
    if (!selectedSw5Field || !selectedShopifyField) {
      toast.error('Bitte wählen Sie beide Felder aus')
      return
    }

    // Check if mapping already exists
    const exists = mapping.some(
      (m) => m.sw5_field === selectedSw5Field && m.shopify_field === selectedShopifyField
    )

    if (exists) {
      toast.error('Dieses Mapping existiert bereits')
      return
    }

    const newMapping: FieldMapping = {
      sw5_field: selectedSw5Field,
      shopify_field: selectedShopifyField,
      transformation: { type: 'direct' },
    }

    onMappingChange([...mapping, newMapping])
    setSelectedSw5Field(null)
    setSelectedShopifyField(null)
    toast.success('Mapping hinzugefügt')
  }

  const removeMapping = (index: number) => {
    const newMapping = mapping.filter((_, i) => i !== index)
    onMappingChange(newMapping)
    toast.success('Mapping entfernt')
  }

  const updateMappingTransformation = (index: number, transformation: TransformationRule) => {
    const newMapping = [...mapping]
    newMapping[index].transformation = transformation
    onMappingChange(newMapping)
    toast.success('Transformation aktualisiert')
  }

  const clearAllMappings = () => {
    if (window.confirm('Möchten Sie wirklich alle Mappings löschen?')) {
      onMappingChange([])
      toast.success('Alle Mappings gelöscht')
    }
  }

  const filteredSw5Fields = sw5Fields.filter((field) =>
    field.path.toLowerCase().includes(sw5SearchTerm.toLowerCase())
  )

  const filteredShopifyFields = shopifyFields.filter((field) =>
    field.path.toLowerCase().includes(shopifySearchTerm.toLowerCase())
  )

  return (
    <div className="card">
      <h2>Field Mapping</h2>

      {/* Produkt-Identifikation Eingabe */}
      <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Felder für bestimmte Produkte laden:
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.25rem', color: '#666' }}>
              {config.sw5Label}:
            </label>
            <input
              type="text"
              className="input"
              placeholder="ID oder Nummer"
              value={articleNumber}
              onChange={(e) => setArticleNumber(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleLoadByIdentifiers()}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.25rem', color: '#666' }}>
              {config.shopifyLabel}:
            </label>
            <input
              type="text"
              className="input"
              placeholder="Produkt-ID oder SKU"
              value={productIdentifier}
              onChange={(e) => setProductIdentifier(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleLoadByIdentifiers()}
            />
          </div>
        </div>
        <button className="button" onClick={handleLoadByIdentifiers} style={{ width: '100%' }}>
          Felder laden
        </button>
        <small style={{ color: '#666', marginTop: '0.5rem', display: 'block' }}>
          Leer lassen, um Felder aus mehreren Produkten zu laden
        </small>
      </div>

      {loading ? (
        <div>Lade Felder...</div>
      ) : (
        <>
          <div style={{ padding: '0.75rem', backgroundColor: '#e8f4f8', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.9rem' }}>
            <strong>Legende:</strong>
            {' '}
            <span style={{ color: 'red', fontWeight: 'bold' }}>*</span> = Pflichtfeld
            {' • '}
            <span style={{ color: 'green' }}>✓</span> = Bereits gemappt
          </div>

          <div className="field-mapping-grid">
            <div>
              <h3>{config.sw5Label} ({sw5Fields.length})</h3>
              <input
                type="text"
                className="input"
                placeholder="Suche..."
                value={sw5SearchTerm}
                onChange={(e) => setSw5SearchTerm(e.target.value)}
                style={{ width: '100%', marginBottom: '0.5rem' }}
              />
              <div className="field-list">
                {filteredSw5Fields.map((field) => (
                  <div
                    key={field.path}
                    className={`field-item ${
                      selectedSw5Field === field.path ? 'selected' : ''
                    }`}
                    onClick={() => setSelectedSw5Field(field.path)}
                  >
                    <div className="field-path">{field.path}</div>
                    <div className="field-type">
                      {field.type}
                         <div className="field-sample-value">
                        {field.sample_value && ` • ${field.sample_value.substring(0, 50)}`}
                          </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3>{config.shopifyLabel} ({shopifyFields.length})</h3>
              <input
                type="text"
                className="input"
                placeholder="Suche..."
                value={shopifySearchTerm}
                onChange={(e) => setShopifySearchTerm(e.target.value)}
                style={{ width: '100%', marginBottom: '0.5rem' }}
              />
              <div className="field-list">
                {filteredShopifyFields.map((field) => {
                  const isRequired = field.required ||
                    field.path === 'title' ||
                    field.path === 'variants[].price'
                  const isMapped = mapping.some(m => m.shopify_field === field.path)

                  return (
                    <div
                      key={field.path}
                      className={`field-item ${
                        selectedShopifyField === field.path ? 'selected' : ''
                      } ${isMapped ? 'mapped' : ''}`}
                      onClick={() => setSelectedShopifyField(field.path)}
                    >
                      <div className="field-path">
                        {field.path}
                        {isRequired && (
                          <span style={{ color: 'red', marginLeft: '0.5rem', fontWeight: 'bold' }}>*</span>
                        )}
                        {isMapped && (
                          <span style={{ color: 'green', marginLeft: '0.5rem' }}>✓</span>
                        )}
                      </div>
                      <div className="field-type">
                        {field.type}
                        {field.description && ` • ${field.description}`}
                   <div className="field-sample-value">
                        {field.sample_value && ` • ${field.sample_value.substring(0, 50)}`}
                          </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
            <button
              className="button"
              onClick={addMapping}
              disabled={!selectedSw5Field || !selectedShopifyField}
            >
              Mapping hinzufügen
            </button>
            <button className="button button-secondary" onClick={loadFields}>
              Felder neu laden
            </button>
          </div>

          <div className="mapping-list">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>Aktive Mappings ({mapping.length})</h3>
              {mapping.length > 0 && (
                <button className="button button-danger" onClick={clearAllMappings}>
                  Alle löschen
                </button>
              )}
            </div>

            {/* Required Fields Validation Message */}
            {(() => {
              const mappedFields = mapping.map(m => m.shopify_field)
              const requiredFields = ['title', 'variants[].price']
              const missingRequired = requiredFields.filter(f => !mappedFields.includes(f))

              if (missingRequired.length > 0) {
                return (
                  <div style={{
                    padding: '1rem',
                    backgroundColor: '#fff3cd',
                    border: '1px solid #ffc107',
                    borderRadius: '4px',
                    marginBottom: '1rem'
                  }}>
                    <strong>⚠️ Fehlende Pflichtfelder:</strong>
                    <ul style={{ marginTop: '0.5rem', marginBottom: 0, paddingLeft: '1.5rem' }}>
                      {missingRequired.map(field => (
                        <li key={field}><code>{field}</code></li>
                      ))}
                    </ul>
                    <small style={{ display: 'block', marginTop: '0.5rem', color: '#856404' }}>
                      Bitte mappen Sie diese Felder, bevor Sie einen Sync durchführen.
                    </small>
                  </div>
                )
              } else if (mapping.length > 0) {
                return (
                  <div style={{
                    padding: '1rem',
                    backgroundColor: '#d4edda',
                    border: '1px solid #28a745',
                    borderRadius: '4px',
                    marginBottom: '1rem',
                    color: '#155724'
                  }}>
                    <strong>✓ Alle Pflichtfelder sind gemappt</strong>
                  </div>
                )
              }
              return null
            })()}

            {mapping.length === 0 ? (
              <p style={{ color: '#666', fontStyle: 'italic' }}>
                Noch keine Mappings definiert. Wählen Sie Felder aus beiden Listen und klicken Sie auf "Mapping hinzufügen".
              </p>
            ) : (
              mapping.map((m, index) => (
                <div key={index} className="mapping-item" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ flex: 1 }}>
                      <strong>SW5:</strong> <code>{m.sw5_field}</code>
                    </div>
                    <div className="mapping-arrow">→</div>
                    <div style={{ flex: 1 }}>
                      <strong>Shopify:</strong> <code>{m.shopify_field}</code>
                    </div>
                    <button
                      className="button button-secondary"
                      onClick={() => setEditingMappingIndex(index)}
                      style={{ marginLeft: '0.5rem', padding: '0.25rem 0.75rem', fontSize: '0.85rem' }}
                    >
                      Transformation
                    </button>
                    <button
                      className="mapping-remove"
                      onClick={() => removeMapping(index)}
                      title="Mapping entfernen"
                    >
                      ×
                    </button>
                  </div>
                  {m.transformation && m.transformation.type !== 'direct' && (
                    <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#e3f2fd', borderRadius: '4px', fontSize: '0.85rem' }}>
                      <strong>Transformation:</strong> {m.transformation.type === 'replace' && `Ersetzen: "${m.transformation.find}" → "${m.transformation.replace}"`}
                      {m.transformation.type === 'regex' && `Regex: /${m.transformation.find}/ → "${m.transformation.replace}"`}
                      {m.transformation.type === 'split_join' && `Split by "${m.transformation.split_delimiter}" → Join with "${m.transformation.join_delimiter}"`}
                      {m.transformation.type === 'custom' && 'Custom Code'}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* Transformation Editor Modal */}
      {editingMappingIndex !== null && (
        <TransformationEditor
          transformation={mapping[editingMappingIndex].transformation || { type: 'direct' }}
          onChange={(transformation) => updateMappingTransformation(editingMappingIndex, transformation)}
          onClose={() => setEditingMappingIndex(null)}
        />
      )}
    </div>
  )
}

export default FieldMapper
