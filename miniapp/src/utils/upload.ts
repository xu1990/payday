/**
 * 图片上传工具 - 上传到腾讯云 COS
 */
import request from './request'

/**
 * 上传单张图片
 * @param filePath 本地文件路径
 * @returns Promise<string> 返回图片 URL
 */
export async function uploadImage(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/user/me/upload-avatar`,
      filePath,
      name: 'file',
      header: {
        // request 会自动添加 token，但 uploadFile 不会，所以需要手动获取
        Authorization: `Bearer ${uni.getStorageSync('payday_token')}`,
      },
      success: res => {
        if (res.statusCode === 200) {
          try {
            const data = JSON.parse(res.data)
            if (data.details?.url) {
              resolve(data.details.url)
            } else {
              reject(new Error('上传失败：响应格式错误'))
            }
          } catch (e) {
            reject(new Error('上传失败：解析响应失败'))
          }
        } else {
          reject(new Error(`上传失败 (${res.statusCode})`))
        }
      },
      fail: err => {
        reject(new Error(err.errMsg || '上传失败'))
      },
    })
  })
}

/**
 * 批量上传图片
 * @param filePaths 本地文件路径数组
 * @returns Promise<string[]> 返回图片 URL 数组
 */
export async function uploadImages(filePaths: string[]): Promise<string[]> {
  const uploadPromises = filePaths.map(path => uploadImage(path))
  return Promise.all(uploadPromises)
}

export default {
  uploadImage,
  uploadImages,
}
