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
