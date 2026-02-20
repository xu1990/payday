/**
 * Toast 提示工具函数单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock uni 全局对象
const mockShowToast = vi.fn()
const mockHideToast = vi.fn()
const mockShowLoading = vi.fn()
const mockHideLoading = vi.fn()

global.uni = {
  showToast: mockShowToast,
  hideToast: mockHideToast,
  showLoading: mockShowLoading,
  hideLoading: mockHideLoading,
} as any

import {
  showSuccess,
  showError,
  showInfo,
  showLoading,
  hideLoading as hideLoadingFn,
  showToast,
} from '@/utils/toast'

describe('Toast 工具函数', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('showSuccess', () => {
    it('应该显示成功提示', () => {
      showSuccess('操作成功')

      expect(mockShowToast).toHaveBeenCalledWith({
        title: '操作成功',
        icon: 'success',
        duration: 2000,
        mask: true,
      })
    })

    it('应该支持自定义时长', () => {
      showSuccess('操作成功', 3000)

      expect(mockShowToast).toHaveBeenCalledWith({
        title: '操作成功',
        icon: 'success',
        duration: 3000,
        mask: true,
      })
    })
  })

  describe('showError', () => {
    it('应该显示错误提示', () => {
      showError('操作失败')

      expect(mockShowToast).toHaveBeenCalledWith({
        title: '操作失败',
        icon: 'error',
        duration: 2000,
        mask: true,
      })
    })

    it('应该支持自定义时长', () => {
      showError('操作失败', 5000)

      expect(mockShowToast).toHaveBeenCalledWith({
        title: '操作失败',
        icon: 'error',
        duration: 5000,
        mask: true,
      })
    })
  })

  describe('showInfo', () => {
    it('应该显示信息提示', () => {
      showInfo('提示信息')

      expect(mockShowToast).toHaveBeenCalledWith({
        title: '提示信息',
        icon: 'none',
        duration: 2000,
        mask: true,
      })
    })

    it('应该支持自定义时长', () => {
      showInfo('提示信息', 1500)

      expect(mockShowToast).toHaveBeenCalledWith({
        title: '提示信息',
        icon: 'none',
        duration: 1500,
        mask: true,
      })
    })
  })

  describe('showLoading', () => {
    it('应该显示加载提示', () => {
      showLoading('加载中...')

      expect(mockShowLoading).toHaveBeenCalledWith({
        title: '加载中...',
        mask: true,
      })
    })

    it('应该支持不遮罩', () => {
      showLoading('加载中...', false)

      expect(mockShowLoading).toHaveBeenCalledWith({
        title: '加载中...',
        mask: false,
      })
    })
  })

  describe('hideLoading', () => {
    it('应该隐藏加载提示', () => {
      hideLoadingFn()

      expect(mockHideLoading).toHaveBeenCalled()
    })
  })

  describe('showToast', () => {
    it('应该支持自定义选项', () => {
      showToast({
        title: '自定义提示',
        icon: 'success',
        duration: 5000,
        mask: false,
      })

      expect(mockShowToast).toHaveBeenCalledWith({
        title: '自定义提示',
        icon: 'success',
        duration: 5000,
        mask: false,
      })
    })
  })
})
