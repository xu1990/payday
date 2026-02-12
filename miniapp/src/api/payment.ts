/**
 * 微信支付 API
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/payment'

/** 创建支付请求 */
export interface CreatePaymentReq {
  order_id: string
}

/** 小程序支付参数 */
export interface WeChatPayParams {
  timeStamp: string
  nonceStr: string
  package: string
  signType: string
  paySign: string
  out_trade_no: string
}

/** 创建支付响应 */
export interface CreatePaymentRes {
  success: boolean
  data?: WeChatPayParams
  message: string
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
    })
  })
}
