import { useState } from 'react'
import type { TransformationRule } from '../types'

interface TransformationEditorProps {
  transformation: TransformationRule
  onChange: (transformation: TransformationRule) => void
  onClose: () => void
}

function TransformationEditor({ transformation, onChange, onClose }: TransformationEditorProps) {
  const [localTransform, setLocalTransform] = useState<TransformationRule>(transformation || {
    type: 'direct'
  })

  const handleSave = () => {
    onChange(localTransform)
    onClose()
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '2rem',
        maxWidth: '600px',
        width: '90%',
        maxHeight: '80vh',
        overflow: 'auto'
      }}>
        <h3 style={{ marginBottom: '1.5rem' }}>Transformations-Regel bearbeiten</h3>

        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="transformType" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Transformations-Typ:
          </label>
          <select
            id="transformType"
            className="select"
            value={localTransform.type}
            onChange={(e) => setLocalTransform({ ...localTransform, type: e.target.value as any })}
            style={{ width: '100%' }}
          >
            <option value="direct">Direkt (keine Transformation)</option>
            <option value="replace">Ersetzen (einfach)</option>
            <option value="regex">Regex Ersetzen</option>
            <option value="split_join">Split & Join (Delimiter ändern)</option>
            <option value="custom">Custom (Python Code)</option>
          </select>
        </div>

        {localTransform.type === 'replace' && (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="find" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Suchen nach:
              </label>
              <input
                id="find"
                type="text"
                className="input"
                value={localTransform.find || ''}
                onChange={(e) => setLocalTransform({ ...localTransform, find: e.target.value })}
                style={{ width: '100%' }}
                placeholder="z.B. Fahrzeugverwendung:"
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="replace" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Ersetzen durch:
              </label>
              <input
                id="replace"
                type="text"
                className="input"
                value={localTransform.replace || ''}
                onChange={(e) => setLocalTransform({ ...localTransform, replace: e.target.value })}
                style={{ width: '100%' }}
                placeholder="z.B. (leer lassen zum Entfernen)"
              />
            </div>
          </>
        )}

        {localTransform.type === 'regex' && (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="find" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Regex Pattern:
              </label>
              <input
                id="find"
                type="text"
                className="input"
                value={localTransform.find || ''}
                onChange={(e) => setLocalTransform({ ...localTransform, find: e.target.value })}
                style={{ width: '100%' }}
                placeholder="z.B. ^Fahrzeugverwendung:"
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="replace" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Ersetzen durch:
              </label>
              <input
                id="replace"
                type="text"
                className="input"
                value={localTransform.replace || ''}
                onChange={(e) => setLocalTransform({ ...localTransform, replace: e.target.value })}
                style={{ width: '100%' }}
                placeholder="z.B. $1 (Regex-Gruppen verwenden)"
              />
            </div>
          </>
        )}

        {localTransform.type === 'split_join' && (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="splitDelim" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Split Delimiter (trennen bei):
              </label>
              <input
                id="splitDelim"
                type="text"
                className="input"
                value={localTransform.split_delimiter || ''}
                onChange={(e) => setLocalTransform({ ...localTransform, split_delimiter: e.target.value })}
                style={{ width: '100%' }}
                placeholder="z.B. |"
              />
              <small style={{ color: '#666' }}>
                Das Zeichen, bei dem der Text getrennt wird
              </small>
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="joinDelim" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Join Delimiter (verbinden mit):
              </label>
              <input
                id="joinDelim"
                type="text"
                className="input"
                value={localTransform.join_delimiter || ''}
                onChange={(e) => setLocalTransform({ ...localTransform, join_delimiter: e.target.value })}
                style={{ width: '100%' }}
                placeholder="z.B. , "
              />
              <small style={{ color: '#666' }}>
                Das Zeichen, mit dem die Teile verbunden werden. Präfixe wie "Fahrzeugverwendung:" werden automatisch entfernt.
              </small>
            </div>
            <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '4px', marginBottom: '1rem' }}>
              <strong>Beispiel:</strong>
              <div style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
                <div><strong>Vorher:</strong> Fahrzeugverwendung:T3 Bus|Fahrzeugverwendung:T3 Pritsche</div>
                <div><strong>Nachher:</strong> T3 Bus, T3 Pritsche</div>
              </div>
            </div>
          </>
        )}

        {localTransform.type === 'custom' && (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="customCode" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Python Code:
              </label>
              <textarea
                id="customCode"
                className="input"
                value={localTransform.custom_code || ''}
                onChange={(e) => setLocalTransform({ ...localTransform, custom_code: e.target.value })}
                style={{ width: '100%', minHeight: '100px', fontFamily: 'monospace' }}
                placeholder="z.B. value.upper()"
              />
              <small style={{ color: '#666' }}>
                Python Expression, die 'value' transformiert. Beispiele: value.upper(), value.replace('a', 'b')
              </small>
            </div>
          </>
        )}

        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          <button className="button button-success" onClick={handleSave}>
            Speichern
          </button>
          <button className="button button-secondary" onClick={onClose}>
            Abbrechen
          </button>
        </div>
      </div>
    </div>
  )
}

export default TransformationEditor
