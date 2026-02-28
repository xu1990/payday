/**
 * 用户地址管理 API
 * User Address Management API
 */
import { request } from '@/utils/request'

const PREFIX = '/admin/user-addresses'

// ==================== Types ====================
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

export interface UserAddressUpdate {
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
  is_active?: boolean
}

export interface UserAddressListParams {
  user_id?: string
  phone?: string
  contact_name?: string
  active_only?: boolean
  page?: number
  page_size?: number
}

export interface UserAddressListResponse {
  items: UserAddress[]
  total: number
  page: number
  page_size: number
}

// ==================== API Functions ====================
/** 获取地址列表 */
export function listAddresses(params?: UserAddressListParams) {
  const query = new URLSearchParams()
  if (params?.user_id) query.set('user_id', params.user_id)
  if (params?.phone) query.set('phone', params.phone)
  if (params?.contact_name) query.set('contact_name', params.contact_name)
  if (params?.active_only) query.set('active_only', 'true')
  if (params?.page) query.set('page', String(params.page))
  if (params?.page_size) query.set('page_size', String(params.page_size))

  const queryString = query.toString()
  return request<UserAddressListResponse>({
    url: queryString ? `${PREFIX}?${queryString}` : PREFIX,
    method: 'GET',
  })
}

/** 获取单个地址详情 */
export function getAddress(addressId: string) {
  return request<UserAddress>({
    url: `${PREFIX}/${addressId}`,
    method: 'GET',
  })
}

/** 更新地址 */
export function updateAddress(addressId: string, data: UserAddressUpdate) {
  return request<UserAddress>({
    url: `${PREFIX}/${addressId}`,
    method: 'PUT',
    data,
  })
}

/** 设置默认地址 */
export function setDefaultAddress(addressId: string) {
  return request<UserAddress>({
    url: `${PREFIX}/${addressId}/set-default`,
    method: 'POST',
  })
}

/** 获取指定用户的所有地址 */
export function getUserAddresses(userId: string, activeOnly = false) {
  const query = activeOnly ? '?active_only=true' : ''
  return request<UserAddress[]>({
    url: `${PREFIX}/users/${userId}/addresses${query}`,
    method: 'GET',
  })
}
