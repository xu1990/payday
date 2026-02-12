/**
 * 验证常量
 * 集中管理所有验证相关的常量和模式
 */

/** 验证模式 */
export const VALIDATION_PATTERNS = {
  /** 薪资区间格式：例如 5000-10000 */
  SALARY_RANGE: /^\d{1,6}-\d{1,6}$/,
} as const

/** 验证限制 */
export const VALIDATION_LIMITS = {
  /** 帖子内容最大长度 */
  MAX_CONTENT_LENGTH: 5000,
  /** 薪资描述最大长度 */
  MAX_SALARY_LENGTH: 50,
  /** 用户昵称最大长度 */
  MAX_NICKNAME_LENGTH: 20,
  /** 标签最大长度 */
  MAX_TAG_LENGTH: 20,
  /** 评论最大长度 */
  MAX_COMMENT_LENGTH: 500,
} as const

/** 错误消息 */
export const VALIDATION_ERRORS = {
  CONTENT_REQUIRED: '请输入内容',
  CONTENT_TOO_LONG: `内容不能超过${VALIDATION_LIMITS.MAX_CONTENT_LENGTH}字`,
  SALARY_FORMAT_INVALID: '工资区间格式：例如5000-10000',
  SALARY_TOO_LONG: `工资描述不能超过${VALIDATION_LIMITS.MAX_SALARY_LENGTH}字`,
} as const
