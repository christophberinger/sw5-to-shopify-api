import { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import ConnectionStatus from './components/ConnectionStatus'
import FieldMapper from './components/FieldMapper'
import ProductSync from './components/ProductSync'
import { loadMapping, saveMapping } from './utils/storage'
import type { FieldMapping } from './types'

function App() {
  const [mapping, setMapping] = useState<FieldMapping[]>([])

  useEffect(() => {
    // Load saved mapping from localStorage
    const savedMapping = loadMapping()
    if (savedMapping.length > 0) {
      setMapping(savedMapping)
    }
  }, [])

  const handleMappingChange = (newMapping: FieldMapping[]) => {
    setMapping(newMapping)
    saveMapping(newMapping)
  }

  return (
    <>
      <Toaster position="top-right" />

      <div className="header">
        <div className="container">
          <h1>SW5 to Shopify Import Tool</h1>
          <p>Artikel aus Shopware 5 (inkl. Pickware-Felder) zu Shopify migrieren</p>
        </div>
      </div>

      <div className="container">
        <ConnectionStatus />

        <FieldMapper
          mapping={mapping}
          onMappingChange={handleMappingChange}
        />

        <ProductSync mapping={mapping} />
      </div>
    </>
  )
}

export default App
