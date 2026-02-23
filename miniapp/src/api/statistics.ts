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

// ==================== Sprint 4.2: 年终奖统计 ====================

/** 年终奖统计 */
export interface YearEndBonusStats {
  year?: number
  total_count: number
  total_amount: number
  average_amount: number
  median_amount: number
  max_amount: number
  min_amount: number
  ranges: {
    '0-5K': number
    '5-10K': number
    '10-20K': number
    '20-50K': number
    '50K+': number
  }
  my_bonus?: {
    count: number
    total_amount: number
    records: Array<{
      id: string
      amount: number
      payday_date: string | null
    }>
  }
}

/** 获取年终奖统计 */
export function getYearEndBonusStats(year?: number) {
  const url = year ? `${PREFIX}/year-end-bonus?year=${year}` : `${PREFIX}/year-end-bonus`
  return request<YearEndBonusStats>({
    url,
    method: 'GET',
  })
}

// ==================== Sprint 4.3: 准时发薪统计 ====================

/** 准时发薪统计 */
export interface OntimePaymentStats {
  year?: number
  total_count: number
  ontime_count: number
  ontime_rate: number
  arrears_count: number
  arrears_rate: number
  avg_delayed_days: number
}

/** 获取准时发薪统计 */
export function getOntimePaymentStats(year?: number) {
  const url = year ? `${PREFIX}/ontime-payment?year=${year}` : `${PREFIX}/ontime-payment`
  return request<OntimePaymentStats>({
    url,
    method: 'GET',
  })
}
