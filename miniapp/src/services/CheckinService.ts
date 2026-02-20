/**
 * 签到服务 - 处理签到相关业务逻辑
 */
import { BaseService } from './base/BaseService'

export interface CheckinItem {
  id: string
  check_date: string
  mood: string
  note: string | null
  created_at: string
}

export interface CheckInStats {
  total_days: number
  current_month_days: number
  today_checked: boolean
}

export interface CalendarItem {
  date: string
  checked: boolean
  mood: string
}

export class CheckinService extends BaseService {
  protected get baseUrl() {
    return '/api/v1/checkin'
  }

  /**
   * 创建签到
   */
  async createCheckIn(data: { mood: string; note?: string }) {
    return this.post<CheckinItem>('', data)
  }

  /**
   * 获取签到统计
   */
  async getStats() {
    return this.get<CheckInStats>('/stats')
  }

  /**
   * 获取签到日历
   */
  async getCalendar(year: number, month: number) {
    return this.get<CalendarItem[]>(`/calendar/${year}/${month}`)
  }

  /**
   * 获取签到记录列表
   */
  async getCheckIns(params: { limit?: number; offset?: number }) {
    return this.get<CheckinItem[]>('', params)
  }
}

// 导出单例
export const checkinService = new CheckinService()
