import axios from 'axios'
import type { Field, FieldMapping, SW5Article, SyncResult } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

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

  validateMapping: async (mapping: FieldMapping[]) => {
    const { data } = await api.get('/mapping/validate', {
      data: mapping,
    })
    return data
  },
}

export default api
