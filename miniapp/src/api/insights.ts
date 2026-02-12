/**
 * 数据洞察 - 与 backend /api/v1/statistics/insights 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/statistics'

/** 分布项 */
export interface DistributionItem {
  label: string
  count: number
  percentage: number
}

/** 行业工资分布 */
export interface IndustryDistribution {
  distribution: DistributionItem[]
  total_users: number
}

/** 城市工资对比 */
export interface CityDistribution {
  distribution: DistributionItem[]
  total_users: number
}

/** 工资区间分布 */
export interface SalaryRangeDistribution {
  distribution: DistributionItem[]
  total_users: number
}

/** 发薪日分布 */
export interface PaydayDistribution {
  distribution: DistributionItem[]
  total_users: number
}

/** 数据洞察响应 */
export interface InsightsData {
  industry_distribution?: IndustryDistribution
  city_distribution?: CityDistribution
  salary_range_distribution?: SalaryRangeDistribution
  payday_distribution?: PaydayDistribution
}

/** 获取数据洞察 */
export function getInsights() {
  return request<InsightsData>({
    url: `${PREFIX}/insights`,
    method: 'GET',
  })
}
