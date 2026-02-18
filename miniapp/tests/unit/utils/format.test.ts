/**
 * 格式化工具函数单元测试
 * 测试日期、金额、数字等格式化功能
 */
import { describe, it, expect } from 'vitest'
import { formatNumber, formatRelativeTime, formatAmount, formatDate, formatDateTime } from '@/utils/format'

describe('格式化工具函数', () => {
  describe('formatNumber', () => {
    it('应该添加千分位分隔符', () => {
      expect(formatNumber(1000)).toBe('1,000')
      expect(formatNumber(10000)).toBe('10,000')
      expect(formatNumber(100000)).toBe('100,000')
      expect(formatNumber(1000000)).toBe('1,000,000')
    })

    it('应该处理小数字', () => {
      expect(formatNumber(999)).toBe('999')
      expect(formatNumber(99)).toBe('99')
      expect(formatNumber(0)).toBe('0')
    })

    it('应该处理 null 和 undefined', () => {
      expect(formatNumber(null)).toBe('0')
      expect(formatNumber(undefined)).toBe('0')
    })

    it('应该处理 NaN', () => {
      expect(formatNumber(NaN)).toBe('0')
    })
  })

  describe('formatAmount', () => {
    it('应该将分转换为元', () => {
      expect(formatAmount(100)).toBe('¥1.00')
      expect(formatAmount(1000)).toBe('¥10.00')
      expect(formatAmount(10000)).toBe('¥100.00')
    })

    it('应该处理 0', () => {
      expect(formatAmount(0)).toBe('¥0.00')
    })

    it('应该处理 null 和 undefined', () => {
      expect(formatAmount(null)).toBe('¥0.00')
      expect(formatAmount(undefined)).toBe('¥0.00')
    })
  })

  describe('formatDate', () => {
    it('应该格式化日期字符串', () => {
      const dateStr = '2026-02-18T12:00:00Z'
      expect(formatDate(dateStr)).toMatch(/\d{4}\/\d{1,2}\/\d{1,2}/)
    })

    it('应该处理空值', () => {
      expect(formatDate(null)).toBe('-')
      expect(formatDate(undefined)).toBe('-')
      expect(formatDate('')).toBe('-')
    })
  })

  describe('formatDateTime', () => {
    it('应该格式化日期时间字符串', () => {
      const dateStr = '2026-02-18T12:00:00Z'
      expect(formatDateTime(dateStr)).toContain('2026')
    })

    it('应该处理空值', () => {
      expect(formatDateTime(null)).toBe('-')
      expect(formatDateTime(undefined)).toBe('-')
    })
  })

  describe('formatRelativeTime', () => {
    it('应该显示"刚刚"对于30秒内的时间', () => {
      const now = new Date()
      const thirtySecondsAgo = new Date(now.getTime() - 30 * 1000).toISOString()
      expect(formatRelativeTime(thirtySecondsAgo)).toBe('刚刚')
    })

    it('应该显示"X分钟前"', () => {
      const now = new Date()
      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000).toISOString()
      expect(formatRelativeTime(fiveMinutesAgo)).toBe('5分钟前')
    })

    it('应该显示"X小时前"', () => {
      const now = new Date()
      const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString()
      expect(formatRelativeTime(twoHoursAgo)).toBe('2小时前')
    })

    it('应该显示"X天前"（7天内）', () => {
      const now = new Date()
      const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString()
      expect(formatRelativeTime(threeDaysAgo)).toBe('3天前')
    })

    it('应该显示日期（7天以上）', () => {
      const oldDate = '2026-02-01T12:00:00Z'
      expect(formatRelativeTime(oldDate)).toMatch(/\d{4}\/\d{1,2}\/\d{1,2}/)
    })

    it('应该处理空值', () => {
      expect(formatRelativeTime(null)).toBe('-')
      expect(formatRelativeTime(undefined)).toBe('-')
      expect(formatRelativeTime('')).toBe('-')
    })
  })
})
