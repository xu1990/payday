#迭代需求如下
1第一笔工资怎么用的
2工资花销出处每月工资花销明细
3晒出你的年终奖，
4发工资能给人带来什么，好处，开心，延迟发，拖欠工资
5每个月目标存多少钱
6加班打卡
7能力值-能力值关联哪些模块
8能力值可以用来获取节假日超市卡，节假日礼包，劳保用品等
9小程序登陆增加登陆授权选择手机号，同一个手机号对应同一个用户

index.js:32 [login] 开始微信授权登录...
index.js:39 [login] uni.login 结果: {errno: , code: "0c3QFUkl2dPleh4tZnol2ENl9u1QFUkI", errMsg: "login:ok"}
index.js:52 [login] 获取到微信授权码
index.js:52 [login] 开始调用后端登录接口...
tokenStorage.js:168 [tokenStorage] Saving token, userId: 09d3dce64c8140a182f00a7f7a7ace0e
tokenStorage.js:172 [tokenStorage] Token saved successfully
tokenStorage.js:189 [tokenStorage] All tokens saved, userId: 09d3dce64c8140a182f00a7f7a7ace0e
tokenStorage.js:37 [tokenStorage] getStorage success for payday_token, attempt 1
tokenStorage.js:126 [tokenStorage] Token retrieved successfully, length: 181
auth.js:76 [authStore] Token verified in storage (attempt 1/5)
index.js:57 [login] 后端登录结果: true
index.js:58 [login] 跳转到首页
index.js:61 App route: 
- path: pages/index
- openType: switchTab
- renderer: webview
- componentFramework: exparser
index.js:61 pages/login/index: onUnload have been invoked
index.js:72 [index] Fetching current user...
vendor.js:3941 Update view with init data
vendor.js:3941 pages/index: onLoad have been invoked
vendor.js:3731 pages/index: onShow have been invoked
tokenStorage.js:37 [tokenStorage] getStorage success for payday_token, attempt 1
tokenStorage.js:126 [tokenStorage] Token retrieved successfully, length: 181
tokenStorage.js:37 [tokenStorage] getStorage success for payday_token, attempt 1
tokenStorage.js:126 [tokenStorage] Token retrieved successfully, length: 181
tokenStorage.js:37 [tokenStorage] getStorage success for payday_refresh_token, attempt 1
tokenStorage.js:37 [tokenStorage] getStorage success for payday_user_id, attempt 1
asyncToGenerator.js:1 Invoke event onReady in page: pages/index
asyncToGenerator.js:1 pages/index: onReady have been invoked
asyncToGenerator.js:1 pages/index: onRouteDone have been invoked
tokenStorage.js:168 [tokenStorage] Saving token, userId: 09d3dce64c8140a182f00a7f7a7ace0e
tokenStorage.js:172 [tokenStorage] Token saved successfully
tokenStorage.js:189 [tokenStorage] All tokens saved, userId: 09d3dce64c8140a182f00a7f7a7ace0e
tokenStorage.js:37 [tokenStorage] getStorage success for payday_token, attempt 1
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
request.js:276 [request] No token available for authenticated request: http://192.168.31.50:8000/api/v1/user/me
_callee3$ @ request.js:276
index.js:77 [index] User fetched successfully
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:43 App route: 
- path: pages/login/index
- openType: reLaunch
- renderer: webview
- componentFramework: exparser
tokenStorage.js:43 pages/index: onUnload have been invoked
vendor.js:3941 Update view with init data
vendor.js:3941 pages/login/index: onLoad have been invoked
vendor.js:3731 pages/login/index: onShow have been invoked
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
index.js:72 [index] Fetching current user...
2tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:43 Invoke event onReady in page: pages/login/index
tokenStorage.js:43 pages/login/index: onReady have been invoked
tokenStorage.js:43 pages/login/index: onRouteDone have been invoked
2tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
request.js:276 [request] No token available for authenticated request: http://192.168.31.50:8000/api/v1/payday
_callee3$ @ request.js:276
index.js:126 [index] loadPaydayData error: {message: "登录已过期，请重新登录", line: 8501, column: 56, sourceURL: "https://usr//app-service.js", stack: "@https://usr//app-service.js:8501:56↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:8511:66↵@https://usr//app-service.js:8511:74↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵_callee$@[native code]↵_callee$@https://usr//app-service.js:8540:56↵@https://usr//app-service.js:2551:2649↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵s@[native code]↵s@https://usr//app-service.js:2551:2899↵@https://usr//app-service.js:2551:8363↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp12@https://usr//app-service.js:2551:8807↵@https://usr//app-service.js:2551:4455↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:2551:4520↵@https://usr//app-service.js:2483:468↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵asyncGeneratorStep@[native code]↵asyncGeneratorStep@https://usr//app-service.js:2483:765↵@https://usr//app-service.js:2483:1483↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵c@[native code]↵c@https://usr//app-service.js:2483:1542↵@https://usr//app-service.js:2483:1782↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:2483:1823↵F@https://lib/WASubContext.js:1:64247↵@https://usr//app-service.js:2483:1163↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp3@https://usr//app-service.js:2483:1887↵@https://usr//app-service.js:8543:47↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵success@[native code]↵success@https://usr//app-service.js:8544:52↵@https://usr//app-service.js:4261:18↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp89@https://usr//app-service.js:4262:36↵@https://lib/WASubContext.js:1:142793↵i@https://lib/WASubContext.js:1:143134↵@https://lib/WAServiceMainContext.js:1:1810761↵p@https://lib/WAServiceMainContext.js:1:444184↵u@https://lib/WAServiceMainContext.js:1:1321860↵@https://lib/WAServiceMainContext.js:1:1559029↵p@https://lib/WAServiceMainContext.js:1:444184↵@https://lib/WAServiceMainContext.js:1:1083339↵forEach@[native code]↵emit@https://lib/WAServiceMainContext.js:1:1083262↵u@https://lib/WAServiceMainContext.js:1:1561463↵Te@https://lib/WAServiceMainContext.js:1:1562737↵@https://lib/WAServiceMainContext.js:1:1563366↵@https://lib/WAServiceMainContext.js:1:1172742↵@https://lib/WAServiceMainContext.js:1:1590670↵@https://lib/WAServiceMainContext.js:1:394271↵_emit@https://lib/WAServiceMainContext.js:1:394187↵emit@https://lib/WAServiceMainContext.js:1:394217↵emit@[native code]↵emit@https://lib/WAServiceMainContext.js:1:393463↵subscribeHandler@https://lib/WAServiceMainContext.js:1:401929"}
_callee2$ @ index.js:126
asyncToGenerator.js:1 App route: 
- path: pages/login/index
- openType: reLaunch
- renderer: webview
- componentFramework: exparser
asyncToGenerator.js:1 pages/login/index: onUnload have been invoked
vendor.js:3941 Update view with init data
vendor.js:3941 pages/login/index: onLoad have been invoked
vendor.js:3731 pages/login/index: onShow have been invoked
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:43 Invoke event onReady in page: pages/login/index
tokenStorage.js:43 pages/login/index: onReady have been invoked
tokenStorage.js:43 pages/login/index: onRouteDone have been invoked
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
request.js:276 [request] No token available for authenticated request: http://192.168.31.50:8000/api/v1/user/me
_callee3$ @ request.js:276
index.js:77 [index] User fetched successfully
asyncToGenerator.js:1 App route: 
- path: pages/login/index
- openType: reLaunch
- renderer: webview
- componentFramework: exparser
asyncToGenerator.js:1 pages/login/index: onUnload have been invoked
vendor.js:3941 Update view with init data
vendor.js:3941 pages/login/index: onLoad have been invoked
vendor.js:3731 pages/login/index: onShow have been invoked
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
2tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
vendor.js:2933 Invoke event onReady in page: pages/login/index
vendor.js:2933 pages/login/index: onReady have been invoked
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:43 pages/login/index: onRouteDone have been invoked
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
asyncToGenerator.js:1 App route: 
- path: pages/index
- openType: reLaunch
- renderer: webview
- componentFramework: exparser
asyncToGenerator.js:1 pages/login/index: onUnload have been invoked
index.js:72 [index] Fetching current user...
vendor.js:3941 Update view with init data
vendor.js:3941 pages/index: onLoad have been invoked
vendor.js:3731 pages/index: onShow have been invoked
2tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
request.js:276 [request] No token available for authenticated request: http://192.168.31.50:8000/api/v1/payday
_callee3$ @ request.js:276
index.js:126 [index] loadPaydayData error: {message: "登录已过期，请重新登录", line: 8501, column: 56, sourceURL: "https://usr//app-service.js", stack: "@https://usr//app-service.js:8501:56↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:8511:66↵@https://usr//app-service.js:8511:74↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵_callee$@[native code]↵_callee$@https://usr//app-service.js:8540:56↵@https://usr//app-service.js:2551:2649↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵s@[native code]↵s@https://usr//app-service.js:2551:2899↵@https://usr//app-service.js:2551:8363↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp12@https://usr//app-service.js:2551:8807↵@https://usr//app-service.js:2551:4455↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:2551:4520↵@https://usr//app-service.js:2483:468↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵asyncGeneratorStep@[native code]↵asyncGeneratorStep@https://usr//app-service.js:2483:765↵@https://usr//app-service.js:2483:1483↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵c@[native code]↵c@https://usr//app-service.js:2483:1542↵@https://usr//app-service.js:2483:1782↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:2483:1823↵F@https://lib/WASubContext.js:1:64247↵@https://usr//app-service.js:2483:1163↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp3@https://usr//app-service.js:2483:1887↵@https://usr//app-service.js:8543:47↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵success@[native code]↵success@https://usr//app-service.js:8544:52↵@https://usr//app-service.js:4261:18↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp89@https://usr//app-service.js:4262:36↵@https://lib/WASubContext.js:1:142793↵i@https://lib/WASubContext.js:1:143134↵@https://lib/WAServiceMainContext.js:1:1810761↵p@https://lib/WAServiceMainContext.js:1:444184↵u@https://lib/WAServiceMainContext.js:1:1321860↵@https://lib/WAServiceMainContext.js:1:1559029↵p@https://lib/WAServiceMainContext.js:1:444184↵@https://lib/WAServiceMainContext.js:1:1083339↵forEach@[native code]↵emit@https://lib/WAServiceMainContext.js:1:1083262↵u@https://lib/WAServiceMainContext.js:1:1561463↵Te@https://lib/WAServiceMainContext.js:1:1562737↵@https://lib/WAServiceMainContext.js:1:1563366↵@https://lib/WAServiceMainContext.js:1:1172742↵@https://lib/WAServiceMainContext.js:1:1590670↵@https://lib/WAServiceMainContext.js:1:394271↵_emit@https://lib/WAServiceMainContext.js:1:394187↵emit@https://lib/WAServiceMainContext.js:1:394217↵emit@[native code]↵emit@https://lib/WAServiceMainContext.js:1:393463↵subscribeHandler@https://lib/WAServiceMainContext.js:1:401929"}
_callee2$ @ index.js:126
2tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
vendor.js:2933 Invoke event onReady in page: pages/index
vendor.js:2933 pages/index: onReady have been invoked
vendor.js:2933 pages/index: onRouteDone have been invoked
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
asyncToGenerator.js:1 App route: 
- path: pages/index
- openType: reLaunch
- renderer: webview
- componentFramework: exparser
asyncToGenerator.js:1 pages/index: onUnload have been invoked
index.js:72 [index] Fetching current user...
vendor.js:3941 Update view with init data
vendor.js:3941 pages/index: onLoad have been invoked
vendor.js:3731 pages/index: onShow have been invoked
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
request.js:276 [request] No token available for authenticated request: http://192.168.31.50:8000/api/v1/user/me
_callee3$ @ request.js:276
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
2index.js:77 [index] User fetched successfully
2tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
vendor.js:2933 Invoke event onReady in page: pages/index
vendor.js:2933 pages/index: onReady have been invoked
vendor.js:2933 pages/index: onRouteDone have been invoked
2tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
tokenStorage.js:43 App route: 
- path: pages/login/index
- openType: reLaunch
- renderer: webview
- componentFramework: exparser
tokenStorage.js:43 pages/index: onUnload have been invoked
vendor.js:3941 Update view with init data
vendor.js:3941 pages/login/index: onLoad have been invoked
vendor.js:3731 pages/login/index: onShow have been invoked
index.js:72 [index] Fetching current user...
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
vendor.js:2933 Invoke event onReady in page: pages/login/index
vendor.js:2933 pages/login/index: onReady have been invoked
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (1/3)
fail @ tokenStorage.js:40
tokenStorage.js:43 pages/login/index: onRouteDone have been invoked
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
request.js:276 [request] No token available for authenticated request: http://192.168.31.50:8000/api/v1/payday
_callee3$ @ request.js:276
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
request.js:276 [request] No token available for authenticated request: http://192.168.31.50:8000/api/v1/payday
_callee3$ @ request.js:276
index.js:126 [index] loadPaydayData error: {message: "登录已过期，请重新登录", line: 8501, column: 56, sourceURL: "https://usr//app-service.js", stack: "@https://usr//app-service.js:8501:56↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:8511:66↵@https://usr//app-service.js:8511:74↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵_callee$@[native code]↵_callee$@https://usr//app-service.js:8540:56↵@https://usr//app-service.js:2551:2649↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵s@[native code]↵s@https://usr//app-service.js:2551:2899↵@https://usr//app-service.js:2551:8363↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp12@https://usr//app-service.js:2551:8807↵@https://usr//app-service.js:2551:4455↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:2551:4520↵@https://usr//app-service.js:2483:468↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵asyncGeneratorStep@[native code]↵asyncGeneratorStep@https://usr//app-service.js:2483:765↵@https://usr//app-service.js:2483:1483↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵c@[native code]↵c@https://usr//app-service.js:2483:1542↵@https://usr//app-service.js:2483:1782↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:2483:1823↵F@https://lib/WASubContext.js:1:64247↵@https://usr//app-service.js:2483:1163↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp3@https://usr//app-service.js:2483:1887↵@https://usr//app-service.js:8543:47↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵success@[native code]↵success@https://usr//app-service.js:8544:52↵@https://usr//app-service.js:4261:18↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp89@https://usr//app-service.js:4262:36↵@https://lib/WASubContext.js:1:142793↵i@https://lib/WASubContext.js:1:143134↵@https://lib/WAServiceMainContext.js:1:1810761↵p@https://lib/WAServiceMainContext.js:1:444184↵u@https://lib/WAServiceMainContext.js:1:1321860↵@https://lib/WAServiceMainContext.js:1:1559029↵p@https://lib/WAServiceMainContext.js:1:444184↵@https://lib/WAServiceMainContext.js:1:1083339↵forEach@[native code]↵emit@https://lib/WAServiceMainContext.js:1:1083262↵u@https://lib/WAServiceMainContext.js:1:1561463↵Te@https://lib/WAServiceMainContext.js:1:1562737↵@https://lib/WAServiceMainContext.js:1:1563366↵@https://lib/WAServiceMainContext.js:1:1172742↵@https://lib/WAServiceMainContext.js:1:1590670↵@https://lib/WAServiceMainContext.js:1:394271↵_emit@https://lib/WAServiceMainContext.js:1:394187↵emit@https://lib/WAServiceMainContext.js:1:394217↵emit@[native code]↵emit@https://lib/WAServiceMainContext.js:1:393463↵subscribeHandler@https://lib/WAServiceMainContext.js:1:401929"}
_callee2$ @ index.js:126
index.js:126 [index] loadPaydayData error: {message: "登录已过期，请重新登录", line: 8501, column: 56, sourceURL: "https://usr//app-service.js", stack: "@https://usr//app-service.js:8501:56↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:8511:66↵@https://usr//app-service.js:8511:74↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵_callee$@[native code]↵_callee$@https://usr//app-service.js:8540:56↵@https://usr//app-service.js:2551:2649↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵s@[native code]↵s@https://usr//app-service.js:2551:2899↵@https://usr//app-service.js:2551:8363↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp12@https://usr//app-service.js:2551:8807↵@https://usr//app-service.js:2551:4455↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:2551:4520↵@https://usr//app-service.js:2483:468↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵asyncGeneratorStep@[native code]↵asyncGeneratorStep@https://usr//app-service.js:2483:765↵@https://usr//app-service.js:2483:1483↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵c@[native code]↵c@https://usr//app-service.js:2483:1542↵@https://usr//app-service.js:2483:1782↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵@https://usr//app-service.js:2483:1823↵F@https://lib/WASubContext.js:1:64247↵@https://usr//app-service.js:2483:1163↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp3@https://usr//app-service.js:2483:1887↵@https://usr//app-service.js:8543:47↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵success@[native code]↵success@https://usr//app-service.js:8544:52↵@https://usr//app-service.js:4261:18↵@[native code]↵l@https://lib/WAServiceMainContext.js:1:41274↵anonymous@[native code]↵_tmp89@https://usr//app-service.js:4262:36↵@https://lib/WASubContext.js:1:142793↵i@https://lib/WASubContext.js:1:143134↵@https://lib/WAServiceMainContext.js:1:1810761↵p@https://lib/WAServiceMainContext.js:1:444184↵u@https://lib/WAServiceMainContext.js:1:1321860↵@https://lib/WAServiceMainContext.js:1:1559029↵p@https://lib/WAServiceMainContext.js:1:444184↵@https://lib/WAServiceMainContext.js:1:1083339↵forEach@[native code]↵emit@https://lib/WAServiceMainContext.js:1:1083262↵u@https://lib/WAServiceMainContext.js:1:1561463↵Te@https://lib/WAServiceMainContext.js:1:1562737↵@https://lib/WAServiceMainContext.js:1:1563366↵@https://lib/WAServiceMainContext.js:1:1172742↵@https://lib/WAServiceMainContext.js:1:1590670↵@https://lib/WAServiceMainContext.js:1:394271↵_emit@https://lib/WAServiceMainContext.js:1:394187↵emit@https://lib/WAServiceMainContext.js:1:394217↵emit@[native code]↵emit@https://lib/WAServiceMainContext.js:1:393463↵subscribeHandler@https://lib/WAServiceMainContext.js:1:401929"}
_callee2$ @ index.js:126
asyncToGenerator.js:1 App route: 
- path: pages/login/index
- openType: reLaunch
- renderer: webview
- componentFramework: exparser
asyncToGenerator.js:1 pages/login/index: onUnload have been invoked
vendor.js:3941 Update view with init data
vendor.js:3941 pages/login/index: onLoad have been invoked
vendor.js:3731 pages/login/index: onShow have been invoked
tokenStorage.js:40 [tokenStorage] getStorage not found for payday_token, retrying (2/3)
fail @ tokenStorage.js:40
index.js:72 [index] Fetching current user...
tokenStorage.js:42 [tokenStorage] getStorage not found for payday_token after 3 attempts
fail @ tokenStorage.js:42
tokenStorage.js:126 [tokenStorage] No token found in storage
_callee4$ @ tokenStorage.js:126
request.js:276 [request] No token available for authenticated request: http://192.168.31.50:8000/api/v1/user/me
_callee3$ @ request.js:276