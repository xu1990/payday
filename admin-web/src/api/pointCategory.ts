/**
 * 积分商品分类管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/admin/point-categories'

// ==================== Types ====================

export interface PointCategory {
  id: string
  name: string
  description: string | null
  parent_id: string | null
  icon_url: string | null
  banner_url: string | null
  level: number
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
  children?: PointCategory[] // Only in tree endpoint
}

export interface PointCategoryCreate {
  name: string
  level: number
  description?: string | null
  parent_id?: string | null
  icon_url?: string | null
  banner_url?: string | null
  sort_order?: number
  is_active?: boolean
}

export interface PointCategoryUpdate {
  name?: string
  description?: string | null
  icon_url?: string | null
  banner_url?: string | null
  sort_order?: number
  is_active?: boolean
}

// ==================== API Functions ====================

/** 获取分类列表（平铺） */
export function listPointCategories(params?: { active_only?: boolean }) {
  const { active_only = false } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
  return request<PointCategory[]>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 获取分类树（层级结构） */
export function getCategoryTree(params?: { active_only?: boolean }) {
  const { active_only = true } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
  return request<PointCategory[]>({
    url: `${PREFIX}/tree?${q.toString()}`,
    method: 'GET',
  })
}

/** 获取单个分类详情 */
export function getPointCategory(categoryId: string) {
  return request<PointCategory>({
    url: `${PREFIX}/${categoryId}`,
    method: 'GET',
  })
}

/** 创建分类 */
export function createPointCategory(data: PointCategoryCreate) {
  return request<{ id: string }>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** 更新分类 */
export function updatePointCategory(categoryId: string, data: PointCategoryUpdate) {
  return request({
    url: `${PREFIX}/${categoryId}`,
    method: 'PUT',
    data,
  })
}

/** 删除分类 */
export function deletePointCategory(categoryId: string) {
  return request({
    url: `${PREFIX}/${categoryId}`,
    method: 'DELETE',
  })
}
