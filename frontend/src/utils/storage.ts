import type { FieldMapping } from '../types'

const STORAGE_KEY = 'sw5_shopify_mapping'

export const saveMapping = (mapping: FieldMapping[]): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mapping))
  } catch (error) {
    console.error('Failed to save mapping to localStorage:', error)
  }
}

export const loadMapping = (): FieldMapping[] => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : []
  } catch (error) {
    console.error('Failed to load mapping from localStorage:', error)
    return []
  }
}

export const clearMapping = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (error) {
    console.error('Failed to clear mapping from localStorage:', error)
  }
}
