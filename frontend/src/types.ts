export interface Field {
  path: string
  type: string
  sample_value?: string
  required?: boolean
  description?: string
}

export interface TransformationRule {
  type: 'direct' | 'replace' | 'regex' | 'split_join' | 'custom'
  find?: string
  replace?: string
  split_delimiter?: string
  join_delimiter?: string
  custom_code?: string
}

export interface FieldMapping {
  sw5_field: string
  shopify_field: string
  transformation?: TransformationRule
}

export interface SW5Article {
  id: number
  name: string
  mainDetail?: {
    number?: string
    prices?: any[]
  }
  [key: string]: any
}

export interface ShopifyProduct {
  id?: number
  title: string
  variants?: Array<{
    sku?: string
    price?: string
    [key: string]: any
  }>
  [key: string]: any
}

export interface SyncResult {
  sw5_article_id: number
  status: string
  success: boolean
  shopify_product_id?: number
  error?: string
}

// Entity Types for multi-entity support
export type EntityType = 'articles' | 'orders' | 'customers'

export interface EntityConfig {
  type: EntityType
  sw5Label: string
  shopifyLabel: string
  syncModes: ('create' | 'update' | 'upsert')[]
}

export const ENTITY_CONFIGS: Record<EntityType, EntityConfig> = {
  articles: {
    type: 'articles',
    sw5Label: 'Shopware 5 Artikel',
    shopifyLabel: 'Shopify Produkte',
    syncModes: ['create', 'update', 'upsert']
  },
  orders: {
    type: 'orders',
    sw5Label: 'Shopware 5 Bestellungen',
    shopifyLabel: 'Shopify Bestellungen',
    syncModes: ['upsert']  // Read-only
  },
  customers: {
    type: 'customers',
    sw5Label: 'Shopware 5 Kunden',
    shopifyLabel: 'Shopify Kunden',
    syncModes: ['create', 'update', 'upsert']
  }
}

// Multi-Entity Mapping Export Format
export interface MappingExport {
  version: string
  exportDate: string
  mappings: {
    articles: FieldMapping[]
    orders: FieldMapping[]
    customers: FieldMapping[]
  }
}
