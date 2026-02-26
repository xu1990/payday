/**
 * 积分商品SKU管理 API
 * Sprint 4.7 - Multi-Specification System
 */
import { request } from '@/utils/request'

const PREFIX = '/admin/point-products'

// ==================== Type Definitions ====================

/** 规格 */
export interface PointSpecification {
  id: string
  product_id: string
  name: string // e.g., "颜色", "尺寸"
  sort_order: number
  values?: PointSpecificationValue[]
}

/** 规格值 */
export interface PointSpecificationValue {
  id: string
  specification_id: string
  value: string // e.g., "红色", "L"
  sort_order: number
}

/** SKU */
export interface PointProductSKU {
  id: string
  product_id: string
  sku_code: string
  specs: Record<string, string> // {"颜色": "红色", "尺寸": "L"}
  stock: number
  stock_unlimited: boolean
  points_cost: number
  image_url?: string
  is_active: boolean
  sort_order: number
}

// ==================== Request/Response Types ====================

export interface SpecificationCreate {
  name: string
  sort_order?: number
}

export interface SpecificationUpdate {
  name?: string
  sort_order?: number
}

export interface SpecificationResponse {
  id: string
  product_id: string
  name: string
  sort_order: number
}

export interface SpecificationValueCreate {
  value: string
  sort_order?: number
}

export interface SpecificationValueUpdate {
  value?: string
  sort_order?: number
}

export interface SpecificationValueResponse {
  id: string
  specification_id: string
  value: string
  sort_order: number
}

export interface SKUCreate {
  sku_code: string
  specs: Record<string, string>
  points_cost: number
  stock: number
  stock_unlimited?: boolean
  image_url?: string
  sort_order?: number
}

export interface SKUUpdate {
  sku_code?: string
  specs?: Record<string, string>
  points_cost?: number
  stock?: number
  stock_unlimited?: boolean
  image_url?: string
  is_active?: boolean
  sort_order?: number
}

export interface SKUResponse {
  id: string
  product_id: string
  sku_code: string
  specs: Record<string, string>
  stock: number
  stock_unlimited: boolean
  points_cost: number
  image_url?: string
  is_active: boolean
  sort_order: number
}

export interface SKUBatchUpdate {
  skus: SKUUpdate[]
}

export interface SpecificationListResult {
  specifications: SpecificationResponse[]
  total: number
}

export interface SpecificationValueListResult {
  values: SpecificationValueResponse[]
  total: number
}

export interface SKUListResult {
  skus: SKUResponse[]
  total: number
}

// ==================== Specification APIs ====================

/** 获取商品规格列表 */
export function listSpecifications(productId: string) {
  return request<SpecificationListResult>({
    url: `${PREFIX}/${productId}/specifications`,
    method: 'GET',
  })
}

/** 创建商品规格 */
export function createSpecification(productId: string, data: SpecificationCreate) {
  return request<{ id: string }>({
    url: `${PREFIX}/${productId}/specifications`,
    method: 'POST',
    data,
  })
}

/** 更新规格 */
export function updateSpecification(specId: string, data: SpecificationUpdate) {
  return request({
    url: `${PREFIX}/specifications/${specId}`,
    method: 'PUT',
    data,
  })
}

/** 删除规格 */
export function deleteSpecification(specId: string) {
  return request({
    url: `${PREFIX}/specifications/${specId}`,
    method: 'DELETE',
  })
}

// ==================== Specification Value APIs ====================

/** 获取规格的值列表 */
export function listSpecificationValues(specificationId: string) {
  return request<SpecificationValueListResult>({
    url: `${PREFIX}/specifications/${specificationId}/values`,
    method: 'GET',
  })
}

/** 创建规格值 */
export function createSpecificationValue(specificationId: string, data: SpecificationValueCreate) {
  return request<{ id: string }>({
    url: `${PREFIX}/specifications/${specificationId}/values`,
    method: 'POST',
    data,
  })
}

/** 更新规格值 */
export function updateSpecificationValue(valueId: string, data: SpecificationValueUpdate) {
  return request({
    url: `${PREFIX}/specification-values/${valueId}`,
    method: 'PUT',
    data,
  })
}

/** 删除规格值 */
export function deleteSpecificationValue(valueId: string) {
  return request({
    url: `${PREFIX}/specification-values/${valueId}`,
    method: 'DELETE',
  })
}

// ==================== SKU APIs ====================

/** 获取商品SKU列表 */
export function listSKUs(productId: string, activeOnly: boolean = false) {
  const q = new URLSearchParams()
  q.set('active_only', String(activeOnly))
  return request<SKUListResult>({
    url: `${PREFIX}/${productId}/skus?${q.toString()}`,
    method: 'GET',
  })
}

/** 创建SKU */
export function createSKU(productId: string, data: SKUCreate) {
  return request<{ id: string }>({
    url: `${PREFIX}/${productId}/skus`,
    method: 'POST',
    data,
  })
}

/** 更新SKU */
export function updateSKU(skuId: string, data: SKUUpdate) {
  return request({
    url: `${PREFIX}/skus/${skuId}`,
    method: 'PUT',
    data,
  })
}

/** 删除SKU */
export function deleteSKU(skuId: string) {
  return request({
    url: `${PREFIX}/skus/${skuId}`,
    method: 'DELETE',
  })
}

/** 批量更新SKU */
export function batchUpdateSKUs(data: SKUBatchUpdate) {
  return request({
    url: `${PREFIX}/skus/batch-update`,
    method: 'POST',
    data,
  })
}
