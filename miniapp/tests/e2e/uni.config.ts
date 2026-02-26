/**
 * uni-app E2E 测试配置
 * 用于微信小程序自动化测试
 */
import { defineConfig } from '@dcloudio/uni-automator'

export default defineConfig({
  /**
   * 微信开发者工具路径
   * macOS: /Applications/wechatwebdevtools.app/Contents/MacOS/cli
   * Windows: C:\\Program Files (x86)\\Tencent\\webwechatdevtools\\cli.bat
   */
  executablePath: process.env.WECHAT_DEVTOOLS_PATH || '/Applications/wechatwebdevtools.app/Contents/MacOS/cli',

  /**
   * 项目路径（编译后的微信小程序路径）
   */
  projectPath: process.env.UNI_INPUT_DIR || './dist/build/mp-weixin',

  /**
   * 测试端口
   */
  port: 9420,

  /**
   * 是否自动重启
   */
  autoRestart: false,

  /**
   * 是否远程调试
   */
  remote: false,

  /**
   * 连接超时时间（毫秒）
   */
  connectTimeout: 60000,

  /**
   * 启动超时时间（毫秒）
   */
  launchTimeout: 120000,

  /**
   * 测试完成后是否关闭开发者工具
   */
  closeAfterEnd: false,
})
