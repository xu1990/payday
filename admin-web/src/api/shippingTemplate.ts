/**
 * Shipping Template Management API
 * 运费模板管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/admin/shipping-templates'

// ==================== Types ====================

export type ChargeType = 'weight' | 'quantity' | 'fixed' | 'volume'

export type FreeShippingType = 'none' | 'amount' | 'quantity' | 'seller'

export interface ExcludedRegion {
  code: string
  name: string
}

export interface ShippingTemplate {
  id: string
  name: string
  description: string | null
  charge_type: ChargeType
  default_first_unit: number | null
  default_first_cost: number | null // in cents
  default_continue_unit: number | null
  default_continue_cost: number | null // in cents
  free_shipping_type: FreeShippingType
  free_threshold: number | null // in cents
  free_quantity: number | null
  excluded_regions: ExcludedRegion[] | null
  volume_unit: number | null
  estimate_days_min: number | null
  estimate_days_max: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ShippingTemplateRegion {
  id: string
  template_id: string
  region_codes: string // comma-separated codes
  region_names: string // comma-separated names
  first_unit: number
  first_cost: number // in cents
  continue_unit: number
  continue_cost: number // in cents
  free_threshold: number | null // in cents
  free_quantity: number | null
  is_excluded: boolean
  is_active: boolean
  created_at: string
}

export interface ShippingTemplateCreate {
  name: string
  description?: string | null
  charge_type: ChargeType
  default_first_unit?: number | null
  default_first_cost?: number | null // in cents
  default_continue_unit?: number | null
  default_continue_cost?: number | null // in cents
  free_shipping_type?: FreeShippingType
  free_threshold?: number | null // in cents
  free_quantity?: number | null
  excluded_regions?: ExcludedRegion[] | null
  volume_unit?: number | null
  estimate_days_min?: number | null
  estimate_days_max?: number | null
}

export interface ShippingTemplateUpdate {
  name?: string
  description?: string | null
  charge_type?: ChargeType
  default_first_unit?: number | null
  default_first_cost?: number | null // in cents
  default_continue_unit?: number | null
  default_continue_cost?: number | null // in cents
  free_shipping_type?: FreeShippingType
  free_threshold?: number | null // in cents
  free_quantity?: number | null
  excluded_regions?: ExcludedRegion[] | null
  volume_unit?: number | null
  estimate_days_min?: number | null
  estimate_days_max?: number | null
  is_active?: boolean
}

export interface ShippingTemplateRegionCreate {
  region_codes: string // comma-separated codes
  region_names: string // comma-separated names
  first_unit: number
  first_cost: number // in cents
  continue_unit: number
  continue_cost: number // in cents
  free_threshold?: number | null // in cents
  free_quantity?: number | null
  is_excluded?: boolean
}

export interface ShippingTemplateRegionUpdate {
  region_codes?: string // comma-separated codes
  region_names?: string // comma-separated names
  first_unit?: number
  first_cost?: number // in cents
  continue_unit?: number
  continue_cost?: number // in cents
  free_threshold?: number | null // in cents
  free_quantity?: number | null
  is_excluded?: boolean
  is_active?: boolean
}

export interface ShippingTemplateListResult {
  items: ShippingTemplate[]
  total: number
}

export interface ShippingTemplateRegionListResult {
  items: ShippingTemplateRegion[]
  total: number
}

// ==================== Template APIs ====================

/** List shipping templates */
export function listShippingTemplates(params?: {
  active_only?: boolean
  limit?: number
  offset?: number
}) {
  const { active_only = false, limit = 20, offset = 0 } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  return request<ShippingTemplateListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** Get shipping template by ID */
export function getShippingTemplate(templateId: string) {
  return request<{ data: ShippingTemplate }>({
    url: `${PREFIX}/${templateId}`,
    method: 'GET',
  })
}

/** Create shipping template */
export function createShippingTemplate(data: ShippingTemplateCreate) {
  return request<{ data: ShippingTemplate }>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** Update shipping template */
export function updateShippingTemplate(templateId: string, data: ShippingTemplateUpdate) {
  return request<{ data: ShippingTemplate }>({
    url: `${PREFIX}/${templateId}`,
    method: 'PUT',
    data,
  })
}

/** Delete shipping template */
export function deleteShippingTemplate(templateId: string) {
  return request<{ data: { deleted: boolean } }>({
    url: `${PREFIX}/${templateId}`,
    method: 'DELETE',
  })
}

// ==================== Region APIs ====================

/** List regions for a template */
export function listTemplateRegions(templateId: string) {
  return request<ShippingTemplateRegionListResult>({
    url: `${PREFIX}/${templateId}/regions`,
    method: 'GET',
  })
}

/** Create region for a template */
export function createTemplateRegion(templateId: string, data: ShippingTemplateRegionCreate) {
  return request<{ data: ShippingTemplateRegion }>({
    url: `${PREFIX}/${templateId}/regions`,
    method: 'POST',
    data,
  })
}

/** Update template region */
export function updateTemplateRegion(regionId: string, data: ShippingTemplateRegionUpdate) {
  return request<{ data: ShippingTemplateRegion }>({
    url: `${PREFIX}/shipping-template-regions/${regionId}`,
    method: 'PUT',
    data,
  })
}

/** Delete template region */
export function deleteTemplateRegion(regionId: string) {
  return request<{ data: { deleted: boolean } }>({
    url: `${PREFIX}/shipping-template-regions/${regionId}`,
    method: 'DELETE',
  })
}

// ==================== Helpers ====================

/** Convert cents to yuan (for display) */
export function centsToYuan(cents: number): number {
  return cents / 100
}

/** Convert yuan to cents (for API) */
export function yuanToCents(yuan: number): number {
  return Math.round(yuan * 100)
}

/** Format charge type for display */
export function formatChargeType(type: ChargeType): string {
  const types: Record<ChargeType, string> = {
    weight: '按重量',
    quantity: '按件数',
    fixed: '固定运费',
    volume: '按体积',
  }
  return types[type] || type
}

/** Get unit label based on charge type */
export function getUnitLabel(chargeType: ChargeType): string {
  const labels: Record<ChargeType, string> = {
    weight: 'g',
    quantity: '件',
    fixed: '',
    volume: 'cm³',
  }
  return labels[chargeType] || ''
}

/** Format free shipping type for display */
export function formatFreeShippingType(type: FreeShippingType): string {
  const types: Record<FreeShippingType, string> = {
    none: '不包邮',
    amount: '满金额包邮',
    quantity: '满件数包邮',
    seller: '卖家承担运费',
  }
  return types[type] || type
}

/** Parse region codes string to array */
export function parseRegionCodes(codesStr: string): string[] {
  return codesStr
    .split(',')
    .map(c => c.trim())
    .filter(Boolean)
}

/** Parse region names string to array */
export function parseRegionNames(namesStr: string): string[] {
  return namesStr
    .split(',')
    .map(n => n.trim())
    .filter(Boolean)
}

/** Join region codes array to string */
export function joinRegionCodes(codes: string[]): string {
  return codes.join(',')
}

/** Join region names array to string */
export function joinRegionNames(names: string[]): string {
  return names.join(',')
}
