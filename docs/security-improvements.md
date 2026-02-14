# 安全改进建议

## 1. CSRF Token 存储改进

### 当前实现
- JWT Token: httpOnly cookie ✅ (安全)
- CSRF Token: localStorage ⚠️ (不够安全)

### 问题
XSS 攻击可能窃取存储在 localStorage 中的 CSRF token

### 推荐方案

#### 方案 A: 双重提交 Cookie 模式（推荐）
**后端改动**:
1. 登录时生成 CSRF token
2. 将 CSRF token 设置为两个 cookie：
   - httpOnly cookie（用于后端验证）
   - 普通 cookie（前端可读取，用于发送）

```python
# 示例代码
response.set_cookie(
    'csrf_token',
    token,
    httponly=True,  # 后端验证用
    secure=True,
    samesite='strict'
)
response.set_cookie(
    'csrf_token_visible',
    token,
    httponly=False,  # 前端读取用
    secure=True,
    samesite='strict'
)
```

**前端改动**:
1. 从 cookie 读取 CSRF token（不需要 localStorage）
2. 在请求头中发送

```typescript
// 从 cookie 读取 CSRF token
function getCsrfToken(): string {
  const match = document.cookie.match(/csrf_token_visible=([^;]+)/)
  return match ? match[1] : ''
}

// 请求时发送
config.headers['X-CSRF-Token'] = getCsrfToken()
```

#### 方案 B: Synchronizer Token Pattern
**后端改动**:
1. 使用 session 存储 CSRF token
2. 请求时验证 token 是否匹配 session

**前端改动**:
1. 登录时从响应头获取 CSRF token
2. 使用内存存储（sessionStorage 或纯内存）
3. 页面刷新时重新获取

#### 方案 C: SameSite Cookie (最简单）
**后端改动**:
1. 完全依赖 SameSite=strict cookie
2. 移除 CSRF token 验证（简化代码）

**优点**:
- 最简单，无需前端改动
- 现代浏览器都支持

**缺点**:
- 不支持旧浏览器
- 跨域场景可能有问题

### 短期建议（当前可做）
1. 添加 Content Security Policy (CSP) 头
2. 实施 XSS 防护措施
3. 定期轮换 CSRF token
4. 缩短 CSRF token 有效期

### 长期建议（需要后端配合）
实现方案 A（双重提交 Cookie 模式）

---

## 2. 其他安全改进

### 2.1 添加安全响应头
在后端添加以下响应头：

```python
# FastAPI 中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    return response
```

### 2.2 实施请求签名验证（可选）
虽然当前 JWT 认证已经足够安全，但对于高敏感操作可以添加：

1. 请求时间戳验证（防止重放攻击）
2. 请求签名验证（HMAC）
3. Nonce 机制

### 2.3 添加审计日志
记录所有敏感操作：
- 登录/登出
- 权限变更
- 数据修改
- 删除操作

---

## 3. 密钥管理改进

### 3.1 密钥轮换机制
实现定期密钥轮换：

```python
class KeyRotationManager:
    def __init__(self):
        self.current_version = 2
        self.previous_versions = [1]

    def rotate_key(self):
        # 生成新密钥
        new_key = generate_secure_key()
        # 保存新密钥为当前版本
        self.current_version += 1
        # 旧密钥保留一段时间用于解密旧数据
        self.previous_versions.append(self.current_version - 1)

    def encrypt_with_rotation(self, data):
        # 使用当前密钥加密，并记录版本
        return encrypt(data, key_version=self.current_version)

    def decrypt_with_rotation(self, encrypted_data, key_version):
        # 根据版本选择正确的密钥解密
        key = self.get_key_by_version(key_version)
        return decrypt(encrypted_data, key)
```

### 3.2 密钥泄露应急流程
1. 立即撤销所有可疑 token
2. 强制所有用户重新登入
3. 轮换所有密钥
4. 审查日志查找泄露原因
5. 实施改进措施防止再次发生

---

## 4. 依赖项安全更新

### 定期更新
```bash
# 检查过时的依赖
pip-audit

# 自动更新依赖
pip install --upgrade -r requirements.txt
npm update
```

### 锁定依赖版本
使用 `requirements.txt` 和 `package-lock.json` 锁定版本

---

## 5. 渗透测试

### 建议工具
1. OWASP ZAP - 自动化安全扫描
2. Burp Suite - 手动测试
3. SQLMap - SQL 注入测试
4. NMap - 端口扫描

### 测试清单
- [ ] SQL 注入测试
- [ ] XSS 测试
- [ ] CSRF 测试
- [ ] 认证绕过测试
- [ ] 速率限制测试
- [ ] 权限提升测试
- [ ] 敏感数据泄露测试

---

**文档版本**: 1.0
**最后更新**: 2026-02-14
**状态**: 待实施
