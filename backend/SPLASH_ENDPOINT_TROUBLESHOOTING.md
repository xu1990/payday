# 开屏配置端点故障排查指南

## 问题现象

```
Request URL: http://192.168.31.50:8000/api/v1/config/public/splash
Request Method: GET
Status Code: 500 Internal Server Error
```

## 快速诊断步骤

### 1. 在远程服务器上运行诊断脚本

SSH 登录到 `192.168.31.50`，然后执行:

```bash
cd /path/to/payDay/backend
python3 scripts/diagnose_splash_endpoint.py
```

该脚本将检查:
- ✓ 数据库连接
- ✓ miniprogram_configs 表是否存在
- ✓ 表结构是否正确
- ✓ splash_config 记录是否存在
- ✓ 端点逻辑测试

### 2. 常见问题及解决方案

#### 问题 1: 表不存在

**诊断输出:**
```
✗ miniprogram_configs 表不存在
```

**解决方案:**
```bash
cd /path/to/payDay/backend
alembic upgrade head
```

#### 问题 2: 表结构不正确

**诊断输出:**
```
✗ 缺少列: is_active
```

**解决方案:**
```bash
# 运行所有待执行的迁移
alembic upgrade head

# 或者重新创建该表的迁移
alembic revision --autogenerate -m "fix miniprogram_configs table"
alembic upgrade head
```

#### 问题 3: 没有 splash_config 记录

**诊断输出:**
```
✗ 没有 splash_config 记录
```

**解决方案:**

通过管理后台 API 创建配置:

```bash
# 使用管理员 token
curl -X POST http://192.168.31.50:8000/api/v1/admin/config/splash \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/splash.jpg",
    "content": "欢迎使用薪日",
    "countdown": 3,
    "is_active": true
  }'
```

或在管理后台界面中创建。

### 3. 查看服务器日志

#### 方法 1: 查看应用日志

```bash
# 查看最近的错误
tail -100 /path/to/payDay/backend/logs/app.log | grep -A 20 "splash"

# 实时监控日志
tail -f /path/to/payDay/backend/logs/app.log | grep splash
```

#### 方法 2: 查看 systemd 服务日志

```bash
# 如果使用 systemd
journalctl -u payday-backend -n 100 --no-pager | grep -A 20 "splash"

# 实时监控
journalctl -u payday-backend -f
```

#### 方法 3: 临时开启 Debug 模式

编辑 `backend/.env`:
```bash
DEBUG=True
```

重启服务后再次请求，响应中会包含详细错误信息:
```json
{
  "success": false,
  "message": "AttributeError: 'NoneType' object has no attribute 'value'",
  "code": "INTERNAL_ERROR"
}
```

**⚠️ 重要:** 生产环境修复后记得关闭 DEBUG!

### 4. 本地测试修复

在本地机器上测试修复后的代码:

```bash
# 1. 确保本地数据库运行
mysql.server start  # macOS
# 或
systemctl start mysql  # Linux

# 2. 运行诊断脚本
cd backend
python3 scripts/diagnose_splash_endpoint.py

# 3. 如果本地测试通过，测试端点
curl http://127.0.0.1:8000/api/v1/config/public/splash

# 4. 提交修复
git add app/api/v1/config.py app/api/v1/admin_config.py
git commit -m "fix: improve splash endpoint error handling"

# 5. 推送到远程服务器
git push origin main
```

### 5. 部署到远程服务器

#### 方法 1: Git Pull (推荐)

```bash
# SSH 到远程服务器
ssh user@192.168.31.50

# 进入项目目录
cd /path/to/payDay

# 拉取最新代码
git pull origin main

# 重启服务
systemctl restart payday-backend
# 或
supervisorctl restart payday-backend
```

#### 方法 2: 手动复制文件

```bash
# 在本地复制修改的文件
scp app/api/v1/config.py user@192.168.31.50:/path/to/payDay/backend/app/api/v1/
scp app/api/v1/admin_config.py user@192.168.31.50:/path/to/payDay/backend/app/api/v1/

# SSH 到远程服务器重启
ssh user@192.168.31.50
systemctl restart payday-backend
```

### 6. 验证修复

```bash
# 测试端点
curl -v http://192.168.31.50:8000/api/v1/config/public/splash

# 预期响应 (200 OK)
{
  "success": true,
  "code": "SUCCESS",
  "message": "开屏配置未启用",
  "data": {
    "image_url": null,
    "content": null,
    "countdown": 3,
    "is_active": false
  }
}
```

## 修改摘要

### 修改的文件

1. **backend/app/api/v1/config.py** (行 58-112)
   - 将合并的条件拆分为独立检查
   - 使用 `getattr()` 添加默认值保护
   - 添加 JSON 解析错误日志

2. **backend/app/api/v1/admin_config.py** (行 548-610)
   - 同样的修复模式

### 修复原理

**原代码 (不安全):**
```python
if not config or not config.value or not config.is_active:
    return ...
```

**新代码 (安全):**
```python
# 1. 先检查对象是否存在
if not config:
    return ...

# 2. 安全地获取属性
config_value = getattr(config, 'value', None)
if not config_value:
    return ...

is_active = getattr(config, 'is_active', False)
if not is_active:
    return ...
```

这样可以:
- 避免 SQLAlchemy 对象属性访问问题
- 提供默认值防止 AttributeError
- 更清晰的错误处理逻辑
- 更好的日志记录

## 需要帮助?

如果上述步骤都无法解决问题，请收集以下信息:

1. **诊断脚本完整输出**
   ```bash
   python3 scripts/diagnose_splash_endpoint.py > diagnostic_output.txt 2>&1
   ```

2. **服务器日志中的错误堆栈**
   ```bash
   grep -A 30 "Unhandled exception" logs/app.log | tail -100
   ```

3. **数据库信息**
   ```bash
   mysql -u root -p -e "USE payday_db; SHOW TABLES LIKE 'miniprogram%';"
   mysql -u root -p -e "USE payday_db; DESCRIBE miniprogram_configs;"
   mysql -u root -p -e "USE payday_db; SELECT * FROM miniprogram_configs WHERE key='splash_config';"
   ```

4. **Python 和依赖版本**
   ```bash
   python3 --version
   pip list | grep -E "(fastapi|sqlalchemy|pydantic)"
   ```
