# 性能监控面板配置指南

## 概述

本指南介绍如何为 PayDay 项目配置 Prometheus + Grafana 性能监控面板。

## 架构图

```
┌─────────────┐      ┌──────────────┐
│  FastAPI   │ ───> │  Prometheus   │
│  Backend   │      │  (Metrics)   │
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                      ┌──────────────┐
                      │   Grafana    │
                      │ (Dashboard)  │
                      └──────────────┘
```

## 组件说明

### 1. Prometheus

**作用**: 收集和存储时间序列数据

**配置文件**: `backend/monitoring/prometheus.yml`

**关键配置**:
- 抓取间隔: 15 秒
- 数据保留: 15 天 / 10GB
- 抓取目标: Backend, Node, MySQL, Redis, Cadvisor

**运行**:
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v ~/payday/backend/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v ~/prometheus-data:/prometheus \
  prom/prometheus:latest
```

访问: `http://localhost:9090`

---

### 2. Grafana

**作用**: 可视化 Prometheus 数据

**仪表板**: `backend/monitoring/grafana-dashboard.json`

**关键面板**:
- 应用健康状态 (UP/DOWN)
- 请求速率 (RPS)
- P95 响应时间
- 错误率百分比
- 数据库连接池使用率
- Redis 命中率
- 系统 CPU 使用率
- 系统内存使用率
- 磁盘空间使用
- 活跃用户数
- 前端 Core Web Vitals

**运行**:
```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -v ~/grafana-data:/var/lib/grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:latest
```

访问: `http://localhost:3000` (admin/admin)

---

### 3. Exporters

**Node Exporter** (系统指标):
```bash
docker run -d \
  --name node-exporter \
  -p 9100:9100 \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /:/rootfs:ro \
  prom/node-exporter:latest
```

**MySQL Exporter** (数据库指标):
```bash
docker run -d \
  --name mysql-exporter \
  -p 9104:9104 \
  -e DATA_SOURCE_NAME="user:password@tcp(mysql:3306)/database" \
  prom/mysqld-exporter:latest
```

**Redis Exporter** (缓存指标):
```bash
docker run -d \
  --name redis-exporter \
  -p 9121:9121 \
  -e REDIS_ADDR="redis:6379" \
  oliver006/redis_exporter:latest
```

**cAdvisor** (容器指标):
```bash
docker run -d \
  --name cadvisor \
  -p 8080:8080 \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:ro \
  -v /sys:/sys:ro \
  -v /var/lib/docker/:/var/lib/docker:ro \
  --link prometheus:prometheus \
  gcr.io/cadvisor/cadvisor:latest
```

---

## Docker Compose 部署

创建 `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./backend/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./backend/monitoring/alerts.yml:/etc/prometheus/alerts.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./backend/monitoring/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

启动:
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 告警配置

### 告警规则文件

**位置**: `backend/monitoring/alerts.yml`

**告警级别**:
- `critical`: 应用宕机、数据库耗尽、连接丢失
- `warning`: 高错误率、高延迟、资源不足
- `info`: 信息性告警

### 告警通道配置

编辑 `prometheus.yml` 中的 `alertmanagers`:

```yaml
alertmanagers:
  - static_configs:
      # 发送到 Alertmanager
      - targets: ['alertmanager:9093']

      # 或直接发送到 Webhook
      - url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        send_resolved: true
```

### 支持的告警通道

1. **Email**:
```yaml
  - email_config:
      to: 'team@example.com'
      from: 'alertmanager@example.com'
      smarthost: 'smtp.example.com:587'
      auth_username: 'alertmanager'
      auth_password: 'password'
```

2. **Slack**:
```yaml
  - slack_api_url: 'https://hooks.slack.com/...'
```

3. **企业微信**:
```yaml
  - webhook_config:
      url: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...'
```

---

## Grafana 配置步骤

### 1. 添加 Prometheus 数据源

1. 登录 Grafana (`http://localhost:3000`)
2. Configuration → Data Sources → Add data source
3. 选择 "Prometheus"
4. 配置:
   - Name: "Prometheus"
   - URL: `http://prometheus:9090`
   - Access: "Server (default)"
5. 点击 "Save & Test"

### 2. 导入仪表板

1. Dashboards → Import
2. 上传 `grafana-dashboard.json`
3. 选择 "Prometheus" 数据源
4. 点击 Import

### 3. 配置自动刷新

- 点击仪表板设置
- 设置 Refresh interval: "30s"
- 启用自动刷新

### 4. 设置告警通知

1. 在仪表板中点击 Alert 图标
2. 配置告警条件
3. 选择通知通道
4. 保存告警规则

---

## 监控指标参考

### 应用指标

| 指标 | 描述 | 正常范围 |
|------|------|---------|
| `up{job="payday-backend"}` | 应用健康 | = 1 |
| `rate(http_requests_total)` | 请求速率 | 稳定或增长 |
| `histogram_quantile(0.95, http_request_duration_seconds_bucket)` | P95 延迟 | < 1s |
| 错误率 | 5xx/total | < 5% |

### 系统指标

| 指标 | 描述 | 告警阈值 |
|------|------|---------|
| CPU 使用率 | node_cpu_seconds_total | > 80% (10min) |
| 内存使用率 | node_memory_MemAvailable_bytes | > 90% (5min) |
| 磁盘可用空间 | node_filesystem_avail_bytes | < 10% (5min) |

### 前端指标

| 指标 | 描述 | 目标 |
|------|------|------|
| LCP | 最大内容绘制 | < 2.5s |
| FID | 首次输入延迟 | < 100ms |
| CLS | 累积布局偏移 | < 0.1 |

---

## 安全配置

### 1. 设置防火墙规则

```bash
# 仅允许内部网络访问监控面板
iptables -A INPUT -p tcp --dport 3000 -s 10.0.0.0/0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 9090 -s 10.0.0.0/0/8 -j ACCEPT
```

### 2. 启用 HTTPS

使用 Nginx 反向代理：

```nginx
location /prometheus/ {
    proxy_pass http://localhost:9090/;
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
}

location /grafana/ {
    proxy_pass http://localhost:3000/;
}
```

### 3. 数据备份

定期备份 Prometheus 数据：

```bash
# 创建备份脚本
#!/bin/bash
docker exec prometheus tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /prometheus
find /backup -mtime +30 -delete  # 保留30天
```

---

## 性能优化

### Prometheus 优化

1. **调整抓取间隔**: 关键指标 10s，非关键 30s
2. **数据保留**: 根据磁盘空间调整（默认 15d）
3. **压缩存储**: 启用 zstd 压缩

### Grafana 优化

1. **查询优化**: 使用时间范围限制
2. **缓存**: 启用查询缓存
3. **聚合**: 使用 recording rules 预计算

---

## 故障排查

### 问题: Prometheus 无法启动

**检查**:
```bash
docker logs prometheus
```

**常见原因**:
- 配置文件语法错误
- 端口被占用
- 磁盘空间不足

### 问题: Grafana 无法连接 Prometheus

**检查**:
1. Prometheus 是否运行: `docker ps | grep prometheus`
2. 网络连通性: `docker exec prometheus wget -O- http://grafana:3000`
3. Grafana 日志: `docker logs grafana`

### 问题: 指标数据缺失

**排查步骤**:
1. 检查 `/metrics` 端点: `curl http://localhost:8000/metrics`
2. 查看 Prometheus targets 页面
3. 检查 exporter 日志

---

## 维护任务

### 日常

- [ ] 每天检查告警状态
- [ ] 每周审查性能趋势
- [ ] 每月清理旧数据

### 每周

- [ ] 检查磁盘空间
- [ ] 审查告警规则有效性
- [ ] 测试告警通道

### 每月

- [ ] 审查 Prometheus 存储
- [ ] 优化慢查询
- [ ] 更新 Grafana 仪表板

---

## 参考资源

- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
- [Node Exporter](https://github.com/prometheus/node_exporter)
- [MySQL Exporter](https://github.com/prometheus/mysqld_exporter)
- [Redis Exporter](https://github.com/oliver006/redis_exporter)
