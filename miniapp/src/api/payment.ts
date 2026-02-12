/**
 * 微信支付 API
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/payment'

/** 创建支付请求 */
export interface CreatePaymentReq {
  order_id: string
}

/** 小程序支付参数 (uni.requestPayment) */
export interface WeChatPayParams {
  timeStamp: string
  nonceStr: string
  package: string
  signType: string
  paySign: string
}

/** 支付订单信息 (用于后端返回) */
export interface PaymentOrderInfo {
  out_trade_no: string
  params: WeChatPayParams
}

/** 创建支付响应 */
export interface CreatePaymentRes {
  success: boolean
  data?: WeChatPayParams
  message: string
}

/** 验证支付结果 */
export interface VerifyPaymentRes {
  success: boolean
  message?: string
}

/**
 * 验证支付结果
 */
export function verifyPayment(orderId: string): Promise<VerifyPaymentRes> {
  return request<VerifyPaymentRes>({
    url: `${PREFIX}/verify/${orderId}`,
    method: 'GET',
  })
}

/** 创建支付 */
export function createPayment(data: CreatePaymentReq) {
  return request<CreatePaymentRes>({
    url: `${PREFIX}/create`,
    method: 'POST',
    data,
  })
}

/** 调起微信支付 */
export function requestWeChatPayment(params: WeChatPayParams): Promise<void> {
  // 验证必要参数
  if (!params.timeStamp || !params.nonceStr || !params.package || !params.signType || !params.paySign) {
    return Promise.reject(new Error('支付参数不完整'))
  }

  // 验证时间戳（防止重放攻击）- 5分钟窗口
  const now = Math.floor(Date.now() / 1000)
  const timestamp = parseInt(params.timeStamp, 10)
  if (isNaN(timestamp) || Math.abs(now - timestamp) > 300) {
    return Promise.reject(new Error('支付参数已过期，请重新获取'))
  }

  // 验证package格式
  if (!params.package.startsWith('prepay_id=')) {
    return Promise.reject(new Error('支付参数格式错误'))
  }

  // 验证signType
  if (!['RSA', 'MD5', 'HMAC-SHA256'].includes(params.signType)) {
    return Promise.reject(new Error('签名类型不支持'))
  }

  // 验证签名长度（基础检查）
  if (params.paySign.length < 32) {
    return Promise.reject(new Error('签名格式异常'))
  }

  return new Promise((resolve, reject) => {
    uni.requestPayment({
      provider: 'wxpay',
      timeStamp: params.timeStamp,
      nonceStr: params.nonceStr,
      package: params.package,
      signType: params.signType,
      paySign: params.paySign,
      success: () => {
        resolve()
      },
      fail: (err: any) => {
        reject(err)
      },
      complete: (res: any) => {
        // 处理边缘情况：既不是success也不是fail的情况
        if (res && res.errMsg !== 'requestPayment:ok' && res.errMsg !== 'requestPayment:fail cancel') {
          console.warn('Payment completed with unexpected status:', res)
        }
      },
    })
  })
}
