/**
 * 积分商城 API - Sprint 4.7
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/point-shop'

// ==================== 类型定义 ====================
export type ProductType = 'virtual' | 'physical' | 'bundle'
export type ShippingMethod = 'express' | 'self_pickup' | 'no_shipping'
export type OrderStatus = 'pending' | 'completed' | 'cancelled' | 'refunded'

// ==================== SKU相关类型 ====================

/** 规格值 */
export interface SpecificationValue {
  id: string
  specification_id: string
  value: string
  sort_order: number
  created_at: string
}

/** 规格定义 */
export interface Specification {
  id: string
  product_id: string
  name: string
  sort_order: number
  created_at: string
  values: SpecificationValue[]
}

/** SKU规格 */
export interface ProductSKU {
  id: string
  product_id: string
  sku_code: string
  specs: { [key: string]: string }  // {"颜色": "红色", "尺寸": "L"}
  stock: number
  stock_unlimited: boolean
  points_cost: number
  image_url: string | null  // 兼容旧版
  image_urls?: string[]  // SKU多图列表
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

// ==================== 商品 ====================

/** 运费模板信息 */
export interface ShippingTemplate {
  id: string
  name: string
  charge_type: string
  free_shipping_type: string
  excluded_regions: string[]
  excluded_region_names: string[]
  delivery_region_names: string[]
  estimate_days_min?: number
  estimate_days_max?: number
}

/** 商品项 */
export interface PointProduct {
  id: string
  name: string
  description: string | null
  image_url: string | null
  image_urls?: string[]
  points_cost: number
  stock: number
  stock_unlimited: boolean
  category: string | null
  category_id?: string
  has_sku: boolean
  product_type: ProductType
  shipping_method: ShippingMethod
  shipping_template_id?: string | null
  shipping_template?: ShippingTemplate  // 运费模板信息
  specifications?: Specification[]  // 规格列表(当has_sku=true时)
  skus?: ProductSKU[]  // SKU列表(当has_sku=true时)
}

/** 商品列表响应 */
export interface PointProductsResponse {
  products: PointProduct[]
  total: number
}

/** 获取商品列表 */
export function getPointProducts(category?: string) {
  const url = category ? `${PREFIX}/products?category=${category}` : `${PREFIX}/products`
  return request<PointProductsResponse>({
    url,
    method: 'GET',
  })
}

/** 获取商品详情 */
export function getPointProduct(productId: string) {
  return request<PointProduct>({
    url: `${PREFIX}/products/${productId}`,
    method: 'GET',
  })
}

// ==================== 地址 ====================

/** 用户地址 */
export interface UserAddress {
  id: string
  user_id: string
  province_code: string
  province_name: string
  city_code: string
  city_name: string
  district_code: string
  district_name: string
  detailed_address: string
  postal_code?: string
  contact_name: string
  contact_phone: string
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 地址列表响应 */
export interface UserAddressesResponse {
  items: UserAddress[]
  total: number
}

/** 创建地址请求 */
export interface AddressCreate {
  province_code: string
  province_name: string
  city_code: string
  city_name: string
  district_code: string
  district_name: string
  detailed_address: string
  postal_code?: string
  contact_name: string
  contact_phone: string
  is_default?: boolean
}

/** 更新地址请求 */
export interface AddressUpdate {
  province_code?: string
  province_name?: string
  city_code?: string
  city_name?: string
  district_code?: string
  district_name?: string
  detailed_address?: string
  postal_code?: string
  contact_name?: string
  contact_phone?: string
  is_default?: boolean
}

/** 获取我的地址列表 */
export function getMyAddresses(activeOnly = true) {
  return request<UserAddressesResponse>({
    url: `/api/v1/user-addresses?active_only=${activeOnly}`,
    method: 'GET',
  })
}

/** 获取地址详情 */
export function getAddress(addressId: string) {
  return request<UserAddress>({
    url: `/api/v1/user-addresses/${addressId}`,
    method: 'GET',
  })
}

/** 创建地址 */
export function createAddress(data: AddressCreate) {
  return request<UserAddress>({
    url: '/api/v1/user-addresses',
    method: 'POST',
    data,
  })
}

/** 更新地址 */
export function updateAddress(addressId: string, data: AddressUpdate) {
  return request<UserAddress>({
    url: `/api/v1/user-addresses/${addressId}`,
    method: 'PUT',
    data,
  })
}

/** 删除地址 */
export function deleteAddress(addressId: string) {
  return request({
    url: `/api/v1/user-addresses/${addressId}`,
    method: 'DELETE',
  })
}

/** 设置默认地址 */
export function setDefaultAddress(addressId: string) {
  return request({
    url: `/api/v1/user-addresses/${addressId}/set-default`,
    method: 'POST',
  })
}

// ==================== 订单 ====================

/** 订单创建请求 */
export interface PointOrderCreate {
  product_id: string
  sku_id?: string
  address_id?: string
  delivery_info?: string
  notes?: string
}

/** 订单项 */
export interface PointOrder {
  id: string
  order_number: string
  product_name: string
  product_image: string | null
  points_cost: number
  status: OrderStatus
  created_at: string
  address_id?: string
  shipment_id?: string
}

/** 订单列表响应 */
export interface PointOrdersResponse {
  orders: PointOrder[]
  total: number
}

/** 创建订单（下单） */
export function createPointOrder(data: PointOrderCreate) {
  return request<PointOrder>({
    url: `${PREFIX}/orders`,
    method: 'POST',
    data,
  })
}

/** 获取我的订单列表 */
export function getMyPointOrders(status?: string, limit = 50, offset = 0) {
  let url = `${PREFIX}/orders?limit=${limit}&offset=${offset}`
  if (status) url += `&status=${status}`
  return request<PointOrdersResponse>({
    url,
    method: 'GET',
  })
}

/** 订单详情（包含更多信息） */
export interface PointOrderDetail extends PointOrder {
  delivery_info?: string
  notes?: string
  notes_admin?: string
  processed_at?: string
}

/** 获取订单详情 */
export function getPointOrderDetail(orderId: string) {
  return request<PointOrderDetail>({
    url: `${PREFIX}/orders/${orderId}`,
    method: 'GET',
  })
}

/** 取消订单 */
export function cancelPointOrder(orderId: string, reason?: string) {
  return request({
    url: `${PREFIX}/orders/${orderId}/cancel`,
    method: 'POST',
    data: reason ? { reason } : undefined,
  })
}
