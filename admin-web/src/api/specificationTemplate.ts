/**
 * 规格模板管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/admin/specification-templates'

// ==================== Types ====================

export interface SpecificationTemplate {
  id: string
  name: string
  description: string | null
  values: string[]
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SpecificationTemplateCreate {
  name: string
  description?: string | null
  values: string[]
  sort_order?: number
  is_active?: boolean
}

export interface SpecificationTemplateUpdate {
  name?: string
  description?: string | null
  values?: string[]
  sort_order?: number
  is_active?: boolean
}

export interface SpecificationTemplateListResult {
  templates: SpecificationTemplate[]
  total: number
}

// ==================== API Functions ====================

/** 获取规格模板列表 */
export function listSpecificationTemplates(params?: { active_only?: boolean }) {
  const { active_only = false } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
  return request<SpecificationTemplateListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 获取单个规格模板详情 */
export function getSpecificationTemplate(templateId: string) {
  return request<SpecificationTemplate>({
    url: `${PREFIX}/${templateId}`,
    method: 'GET',
  })
}

/** 创建规格模板 */
export function createSpecificationTemplate(data: SpecificationTemplateCreate) {
  return request<{ id: string }>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** 更新规格模板 */
export function updateSpecificationTemplate(templateId: string, data: SpecificationTemplateUpdate) {
  return request({
    url: `${PREFIX}/${templateId}`,
    method: 'PUT',
    data,
  })
}

/** 删除规格模板 */
export function deleteSpecificationTemplate(templateId: string) {
  return request<{ deleted: boolean }>({
    url: `${PREFIX}/${templateId}`,
    method: 'DELETE',
  })
}
