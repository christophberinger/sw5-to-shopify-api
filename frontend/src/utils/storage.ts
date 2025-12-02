import type { FieldMapping, EntityType, MappingExport } from '../types'

const STORAGE_PREFIX = 'sw5_shopify_mapping'
const EXPORT_VERSION = '1.0'

// ==================== PER-ENTITY STORAGE ====================

export const saveMapping = (entityType: EntityType, mapping: FieldMapping[]): void => {
  try {
    const key = `${STORAGE_PREFIX}_${entityType}`
    localStorage.setItem(key, JSON.stringify(mapping))
  } catch (error) {
    console.error(`Failed to save ${entityType} mapping to localStorage:`, error)
  }
}

export const loadMapping = (entityType: EntityType): FieldMapping[] => {
  try {
    const key = `${STORAGE_PREFIX}_${entityType}`
    const saved = localStorage.getItem(key)
    return saved ? JSON.parse(saved) : []
  } catch (error) {
    console.error(`Failed to load ${entityType} mapping from localStorage:`, error)
    return []
  }
}

export const clearMapping = (entityType: EntityType): void => {
  try {
    const key = `${STORAGE_PREFIX}_${entityType}`
    localStorage.removeItem(key)
  } catch (error) {
    console.error(`Failed to clear ${entityType} mapping from localStorage:`, error)
  }
}

// ==================== IMPORT/EXPORT ALL MAPPINGS ====================

export const exportAllMappings = (): MappingExport => {
  return {
    version: EXPORT_VERSION,
    exportDate: new Date().toISOString(),
    mappings: {
      articles: loadMapping('articles'),
      orders: loadMapping('orders'),
      customers: loadMapping('customers')
    }
  }
}

export const importAllMappings = (data: MappingExport): void => {
  if (data.version !== EXPORT_VERSION) {
    throw new Error(`Incompatible export version: ${data.version}. Expected: ${EXPORT_VERSION}`)
  }

  saveMapping('articles', data.mappings.articles || [])
  saveMapping('orders', data.mappings.orders || [])
  saveMapping('customers', data.mappings.customers || [])
}

export const downloadMappingsAsJson = (): void => {
  try {
    const data = exportAllMappings()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sw5-shopify-mappings-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download mappings:', error)
    throw error
  }
}

export const uploadMappingsFromJson = (file: File): Promise<void> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const data: MappingExport = JSON.parse(content)
        importAllMappings(data)
        resolve()
      } catch (error) {
        reject(new Error(`Failed to import mappings: ${error}`))
      }
    }

    reader.onerror = () => {
      reject(new Error('Failed to read file'))
    }

    reader.readAsText(file)
  })
}

// ==================== MIGRATION LOGIC ====================

export const migrateOldMappings = (): void => {
  try {
    const oldKey = 'sw5_shopify_mapping'
    const oldMappings = localStorage.getItem(oldKey)

    // Check if old mappings exist and new articles mapping doesn't
    if (oldMappings && !localStorage.getItem(`${STORAGE_PREFIX}_articles`)) {
      console.log('Migrating old mappings to new format...')
      // Migrate to new format
      localStorage.setItem(`${STORAGE_PREFIX}_articles`, oldMappings)
      localStorage.removeItem(oldKey)
      console.log('Migration complete: old mappings moved to articles')
    }
  } catch (error) {
    console.error('Failed to migrate old mappings:', error)
  }
}
