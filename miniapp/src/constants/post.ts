/**
 * 帖子相关常量
 */

/** 发帖可见性类型 */
export type PostVisibility = 'public' | 'followers' | 'private'

/** 发帖可见性选项 */
export const VISIBILITY_OPTIONS: { value: PostVisibility; label: string; description: string }[] = [
  { value: 'public', label: '公开', description: '所有人可见' },
  { value: 'followers', label: '关注者', description: '仅关注你的人可见' },
  { value: 'private', label: '私密', description: '仅自己可见' },
]

/** 行业选项 */
export const INDUSTRY_OPTIONS = [
  '互联网', '金融', '教育', '医疗', '制造业',
  '房地产', '零售', '物流', '餐饮', '服务业',
  '文化传媒', '广告', '咨询', '法律', '会计',
  '建筑', '能源', '化工', '汽车', '电子',
  '通信', '软件', '硬件', '其他'
]

/** 城市选项（主要城市） */
export const CITY_OPTIONS = [
  '北京', '上海', '广州', '深圳', '杭州',
  '成都', '重庆', '武汉', '西安', '南京',
  '苏州', '天津', '长沙', '郑州', '东莞',
  '青岛', '沈阳', '宁波', '昆明', '合肥',
  '福州', '厦门', '济南', '大连', '哈尔滨',
  '长春', '石家庄', '南宁', '贵阳', '太原',
  '南昌', '金华', '温州', '嘉兴', '其他'
]

/** 薪资范围选项 */
export const SALARY_RANGE_OPTIONS = [
  '3000以下', '3000-5000', '5000-8000', '8000-12000',
  '12000-20000', '20000-30000', '30000-50000', '50000以上'
]
