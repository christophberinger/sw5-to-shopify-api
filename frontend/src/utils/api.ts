import axios from 'axios'
import type { Field, FieldMapping, SW5Article, SyncResult, EntityType } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// ==================== GENERIC ENTITY API ====================

export const entityApi = {
  testConnection: async (entityType: EntityType) => {
    const { data } = await api.get(`/${entityType}/test`)
    return data
  },

  getFields: async (entityType: EntityType, system: 'shopware' | 'shopify', identifier?: string): Promise<Field[]> => {
    const endpoint = `/${entityType}/${system}/fields`
    const params = identifier ? { identifier } : {}
    const { data } = await api.get(endpoint, { params })
    return data.fields || []
  },

  getEntities: async (entityType: EntityType, system: 'shopware' | 'shopify', limit: number = 50, offset: number = 0) => {
    const endpoint = system === 'shopware'
      ? `/${entityType}/shopware/${entityType}`
      : `/${entityType}/shopify/${entityType}`

    const { data } = await api.get(endpoint, {
      params: { limit, offset },
    })
    return data
  },

  getEntity: async (entityType: EntityType, system: 'shopware' | 'shopify', id: number) => {
    const endpoint = `/${entityType}/${system}/${entityType}/${id}`
    const { data } = await api.get(endpoint)
    return data
  },
}

// ==================== LEGACY SHOPWARE API (for backwards compatibility) ====================

export const shopwareApi = {
  testConnection: async () => {
    const { data } = await api.get('/shopware/test')
    return data
  },

  getArticles: async (limit = 50, offset = 0) => {
    const { data } = await api.get('/shopware/articles', {
      params: { limit, offset },
    })
    return data
  },

  getArticle: async (id: number): Promise<SW5Article> => {
    const { data } = await api.get(`/shopware/articles/${id}`)
    return data
  },

  getFields: async (articleNumber?: string): Promise<Field[]> => {
    const params = articleNumber ? { article_number: articleNumber } : {}
    const { data } = await api.get('/shopware/fields', { params })
    return data.fields
  },

  getPickwareFields: async (articleId: number) => {
    const { data } = await api.get(`/shopware/articles/${articleId}/pickware`)
    return data
  },
}

// ==================== LEGACY SHOPIFY API (for backwards compatibility) ====================

export const shopifyApi = {
  testConnection: async () => {
    const { data } = await api.get('/shopify/test')
    return data
  },

  getProducts: async (limit = 50) => {
    const { data } = await api.get('/shopify/products', {
      params: { limit },
    })
    return data
  },

  getFields: async (productIdentifier?: string): Promise<Field[]> => {
    const params = productIdentifier ? { product_identifier: productIdentifier } : {}
    const { data } = await api.get('/shopify/fields', { params })
    return data.fields
  },

  findProductBySku: async (sku: string) => {
    const { data } = await api.get(`/shopify/products/find-by-sku/${sku}`)
    return data
  },
}

// ==================== MAPPING API (entity-aware) ====================

export const mappingApi = {
  transformProduct: async (articleId: number, mapping: FieldMapping[]) => {
    const { data } = await api.post('/mapping/transform', {
      sw5_article_id: articleId,
      mapping,
    })
    return data
  },

  syncProducts: async (
    articleIds: (number | string)[],
    mapping: FieldMapping[],
    mode: 'create' | 'update' | 'upsert' = 'upsert'
  ): Promise<{ total: number; successful: number; failed: number; results: SyncResult[] }> => {
    const { data } = await api.post('/mapping/sync', {
      sw5_article_ids: articleIds,
      mapping,
      mode,
    })
    return data
  },

  // Generic sync for all entity types
  sync: async (
    entityType: EntityType,
    ids: (number | string)[],
    mapping: FieldMapping[],
    mode: 'create' | 'update' | 'upsert' = 'upsert'
  ): Promise<{ total: number; successful: number; failed: number; results: SyncResult[] }> => {
    const { data } = await api.post('/mapping/sync', {
      entity_type: entityType,
      sw5_ids: ids,
      mapping,
      mode,
    })
    return data
  },

  validateMapping: async (mapping: FieldMapping[]) => {
    const { data } = await api.get('/mapping/validate', {
      data: mapping,
    })
    return data
  },
}

export default api
