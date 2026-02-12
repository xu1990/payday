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

// ==================== 数据洞察 ====================

/** 行业分布项 */
export interface IndustryDistribution {
  industry: string | null
  count: number
  avg_amount: number
}

/** 城市分布项 */
export interface CityDistribution {
  city: string | null
  count: number
  avg_amount: number
}

/** 工资区间分布项 */
export interface SalaryRangeDistribution {
  range: string | null
  count: number
}

/** 发薪日分布项 */
export interface PaydayDistribution {
  day: number
  count: number
}

/** 数据洞察响应 */
export interface InsightsData {
  industry: IndustryDistribution[]
  city: CityDistribution[]
  salary_range: SalaryRangeDistribution[]
  payday: PaydayDistribution[]
}

/** 获取数据洞察（行业/城市/工资区间/发薪日分布） */
export function getInsights() {
  return request<InsightsData>({
    url: `${PREFIX}/insights`,
    method: 'GET',
  })
}
