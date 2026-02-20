/**
 * 签到 - 与 backend /api/v1/checkin 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/checkin'

/** 打卡创建请求 */
export interface CheckInCreateReq {
  check_date: string // ISO date string
  note?: string
}

/** 打卡响应 */
export interface CheckInRes {
  id: string
  check_date: string
  note: string | null
}

/** 打卡日历项 */
export interface CalendarItem {
  date: string
  checked: boolean
  note?: string
}

/** 打卡日历响应 */
export interface CalendarRes {
  items: CalendarItem[]
}

/** 打卡统计响应 */
export interface CheckInStatsRes {
  total_days: number
  this_month: number
  current_streak: number
}

/** 创建打卡 */
export function createCheckIn(data: CheckInCreateReq) {
  return request<CheckInRes>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** 获取打卡日历 */
export function getCheckInCalendar(year: number, month: number) {
  return request<CalendarRes>({
    url: `${PREFIX}/calendar?year=${year}&month=${month}`,
    method: 'GET',
  })
}

/** 获取打卡统计 */
export function getCheckInStats() {
  return request<CheckInStatsRes>({
    url: `${PREFIX}/stats`,
    method: 'GET',
  })
}

/** 打卡列表项（用于用户主页展示） */
export interface CheckinItem {
  id: string
  check_date: string
  note: string | null
}

/** 打卡列表响应 */
export interface CheckinListRes {
  items: CheckinItem[]
  total: number
}

/** 获取打卡列表（分页） */
export function getCheckinList(params: { limit?: number; offset?: number }): Promise<CheckinListRes> {
  const { limit = 30, offset = 0 } = params
  return request<CheckinListRes>({
    url: `${PREFIX}/list?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}
