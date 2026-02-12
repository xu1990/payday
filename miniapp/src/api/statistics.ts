/**
 * 统计 - 与 backend /api/v1/statistics 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/statistics'

/** 本月汇总 */
export interface MonthSummary {
  year: number
  month: number
  total_amount: number
  record_count: number
}

/** 近 N 月趋势项（与 MonthSummary 一致） */
export type TrendItem = MonthSummary

/** 本月汇总 */
export function getSummary(year: number, month: number) {
  return request<MonthSummary>({
    url: `${PREFIX}/summary?year=${year}&month=${month}`,
    method: 'GET',
  })
}

/** 近 N 月趋势（默认 6） */
export function getTrend(months: number = 6) {
  return request<TrendItem[]>({
    url: `${PREFIX}/trend?months=${months}`,
    method: 'GET',
  })
}
