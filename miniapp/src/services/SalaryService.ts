/**
 * 薪资服务 - 处理薪资相关业务逻辑
 */
import { BaseService } from './base/BaseService'
import type { SalaryRecord, PaydayConfig } from '@/api/salary'

export class SalaryService extends BaseService {
  protected get baseUrl() {
    return '/api/v1/salary'
  }

  /**
   * 获取薪资记录列表
   */
  async getSalaryRecords(params: {
    config_id?: string
    from_date?: string
    to_date?: string
    limit?: number
    offset?: number
  }) {
    return this.get<SalaryRecord[]>('', params)
  }

  /**
   * 创建薪资记录
   */
  async createSalary(data: {
    config_id: string
    amount: number
    payday_date: string
    salary_type: string
    images?: string[]
    note?: string
    mood: string
  }) {
    return this.post<SalaryRecord>('', data)
  }

  /**
   * 删除薪资记录
   */
  async deleteSalary(recordId: string) {
    return this.delete<boolean>(`/${recordId}`)
  }

  /**
   * 获取发薪日配置列表
   */
  async getPaydayConfigs() {
    return this.get<PaydayConfig[]>('/paydays')
  }
}

// 导出单例
export const salaryService = new SalaryService()
