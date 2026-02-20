# Like Status, Follow Buttons, and Notifications Enhancement - Deployment Guide

**Date**: 2026-02-20
**Version**: 1.0
**Status**: Production Ready ✅

## Overview

This guide provides step-by-step instructions for deploying the like status, follow buttons, and notification enhancements to production. The deployment is **zero-downtime** and **backward compatible**.

## Pre-Deployment Checklist

### 1. Prerequisites Verification

```bash
# Backend: Check Python version (3.9+ required)
cd /Users/a1234/Documents/workspace/payDay/backend
python3 --version

# Backend: Check dependencies are installed
pip list | grep -E "(fastapi|sqlalchemy|redis|pytest)"

# Frontend: Check Node version (16+ recommended)
cd /Users/a1234/Documents/workspace/payDay/miniapp
node --version
npm --version

# Verify Redis is running
redis-cli ping  # Should return PONG

# Verify MySQL is accessible
mysql -u root -p -e "SELECT VERSION();"
```

### 2. Current System Status

```bash
# Check current git branch
cd /Users/a1234/Documents/workspace/payDay
git branch --show-current

# Check for uncommitted changes
git status

# Verify all tests pass locally
cd backend && pytest -q
cd ../miniapp && npm run test
```

### 3. Backup Current State

```bash
# Backup database (adjust command as needed)
mysqldump -u root -p payday_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup current backend code
cd /Users/a1234/Documents/workspace/payDay
git tag backup-before-$(date +%Y%m%d)

# Document current running versions
cd backend && git log -1 --oneline
cd ../miniapp && git log -1 --oneline
```

## Deployment Strategy

### Deployment Type: Blue-Green Deployment

This deployment uses blue-green strategy:
- **Blue**: Current production version
- **Green**: New version with enhancements
- **Switch**: Instant traffic switch when green is verified

### Rollback Plan

If issues occur:
1. **Backend**: Revert to previous commit (see Rollback Procedures below)
2. **Frontend**: WeChat mini-program can be rolled back via MP platform
3. **Database**: No migrations needed - safe to rollback

## Step-by-Step Deployment

### Phase 1: Backend Deployment

#### Step 1.1: Pull Latest Code

```bash
cd /Users/a1234/Documents/workspace/payDay

# Ensure we're on main branch
git checkout main

# Pull latest changes
git pull origin main

# Verify the enhancement commits are present
git log --oneline -15 | grep -E "(is_liked|follow.*status|notification)"
```

Expected output should include:
- `feat: add is_liked field to PostResponse schema`
- `feat: populate is_liked field in post service`
- `feat: add batch follow status endpoint`
- `feat: add follow notification support`

#### Step 1.2: Install Backend Dependencies

```bash
cd backend

# Install/update dependencies
pip install -r requirements.txt

# Verify no dependency conflicts
pip check
```

#### Step 1.3: Run Backend Tests

```bash
cd backend

# Run all tests with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Expected: 150/150 tests passing
# Coverage should be > 80%
```

If tests fail:
```bash
# Run with verbose output to see failures
pytest -v

# Do NOT proceed if tests fail
# Investigate and fix issues before continuing
```

#### Step 1.4: Verify Backend Configuration

```bash
# Check environment variables
cd backend
cat .env | grep -E "(MYSQL|REDIS|JWT|ENCRYPTION)"

# Verify critical settings:
# - MYSQL_HOST, MYSQL_DATABASE
# - REDIS_URL
# - JWT_SECRET_KEY
# - ENCRYPTION_SECRET_KEY
```

#### Step 1.5: Lint and Format Check

```bash
# From project root
cd /Users/a1234/Documents/workspace/payDay

# Run backend linting
npm run lint:backend

# Run backend formatting check
npm run format:backend
```

If linting fails, fix issues:
```bash
# Auto-format with black and isort
cd backend
black app/
isort app/
```

#### Step 1.6: Deploy Backend Code

**Option A: Direct Deployment (Development/Staging)**

```bash
cd backend

# Stop current service (adjust command as needed)
# pkill -f uvicorn
# or: systemctl stop payday-backend

# Start new service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Verify service is running
curl http://localhost:8000/api/v1/health
```

**Option B: Systemd Service (Production)**

```bash
# Create/update systemd service file
sudo nano /etc/systemd/system/payday-backend.service
```

Service file content:
```ini
[Unit]
Description=PayDay Backend API
After=network.target mysql.service redis.service

[Service]
Type=notify
User=payday
Group=payday
WorkingDirectory=/path/to/payDay/backend
Environment="PATH=/path/to/payday/backend/venv/bin"
ExecStart=/path/to/payday/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd and restart service
sudo systemctl daemon-reload
sudo systemctl enable payday-backend
sudo systemctl restart payday-backend

# Check service status
sudo systemctl status payday-backend

# View logs
sudo journalctl -u payday-backend -f
```

#### Step 1.7: Verify Backend Deployment

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test post list endpoint (anonymous)
curl http://localhost:8000/api/v1/posts?limit=1

# Test post list endpoint (authenticated)
# First get a token, then:
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/posts?limit=1 | jq '.data[0].is_liked'

# Should return: true or false (not null/undefined)
```

#### Step 1.8: Verify New Endpoints

```bash
# Test batch follow status endpoint
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": ["user-id-1", "user-id-2"]}' \
  http://localhost:8000/api/v1/follows/status | jq '.'
```

Expected response:
```json
{
  "code": 0,
  "message": "获取关注状态成功",
  "data": {
    "user-id-1": true,
    "user-id-2": false
  }
}
```

### Phase 2: Frontend Deployment

#### Step 2.1: Pull Latest Code

```bash
cd /Users/a1234/Documents/workspace/payDay/miniapp

# Ensure we're on main branch
git checkout main

# Pull latest changes
git pull origin main

# Verify the enhancement commits are present
git log --oneline -10 | grep -E "(is_liked|FollowButton|notification|unread)"
```

Expected output should include:
- `feat: add is_liked field to PostItem interface`
- `feat: use API is_liked in square page, add follow button`
- `feat: add useNotificationUnread composable with polling`
- `feat: add notification tab to AppFooter with unread badge`

#### Step 2.2: Install Frontend Dependencies

```bash
cd miniapp

# Install dependencies
npm install

# Verify no security vulnerabilities
npm audit

# If vulnerabilities found, fix them:
npm audit fix
```

#### Step 2.3: Run Frontend Tests

```bash
cd miniapp

# Run all tests
npm run test

# Expected: 107/107 tests passing

# Run with coverage
npm run test:coverage
```

If tests fail:
```bash
# Run with verbose output
npm run test -- --reporter=verbose

# Do NOT proceed if tests fail
```

#### Step 2.4: Type Checking

```bash
cd miniapp

# Run TypeScript type check
npm run type-check

# Should complete without errors
```

#### Step 2.5: Lint and Format Check

```bash
# From project root
cd /Users/a1234/Documents/workspace/payDay

# Run miniapp linting
npm run lint:miniapp

# Run miniapp formatting
npm run format:miniapp
```

If linting fails, fix issues:
```bash
cd miniapp
npm run lint:miniapp -- --fix
```

#### Step 2.6: Build Mini-Program

```bash
cd miniapp

# Build for production
npm run build:mp-weixin

# Verify build output
ls -la dist/build/mp-weixin/
```

Expected build output:
```
app.js
app.json
app.wxss
pages/
  square/index.js
  post-detail/index.js
  notification/list.js
  profile/index.js
components/
  AppFooter.vue
  FollowButton.vue
  PostActionBar.vue
...
```

#### Step 2.7: Deploy to WeChat Platform

**Manual Upload via WeChat DevTools**:

1. Open WeChat DevTools
2. Import project: `/Users/a1234/Documents/workspace/payDay/miniapp`
3. Click "Upload" button
4. Fill in version number (e.g., `1.2.0`)
5. Fill in project notes:
   ```
   新功能：
   - 帖子列表显示点赞状态
   - 帖子详情显示点赞状态
   - 添加关注按钮（广场和详情页）
   - 消息通知实时更新
   - 添加关注通知类型
   ```
6. Click "Upload"

#### Step 2.8: Submit for Review

1. Go to [WeChat MP Platform](https://mp.weixin.qq.com/)
2. Navigate to: Development → Development Management → Development Versions
3. Find the uploaded version (1.2.0)
4. Click "Submit for Review"
5. Fill in review notes:
   ```
   本次更新优化了社交互动体验：
   1. 帖子列表和详情页显示点赞状态
   2. 添加关注按钮，方便关注感兴趣的作者
   3. 消息通知实时更新，不遗漏重要动态
   4. 新增关注通知类型
   ```
6. Select testing users (if applicable)
7. Submit

**Note**: WeChat review typically takes 1-3 business days.

#### Step 2.9: Test in WeChat DevTools

While waiting for review, test locally:

```bash
# Open WeChat DevTools
# Import project from: /Users/a1234/Documents/workspace/payDay/miniapp

# Test the following flows:
1. Square page - verify like status shows
2. Post detail - verify like button shows correct state
3. Square page - verify follow buttons appear
4. Post detail - verify follow button appears
5. Profile page - verify notification badge shows
6. Click notification tab - verify navigation works
7. Notification list - verify unread count shows
8. Like/unlike posts - verify optimistic updates
9. Follow/unfollow users - verify button changes
```

### Phase 3: Smoke Testing

#### Step 3.1: Backend Smoke Tests

```bash
# Set test variables
BACKEND_URL="http://localhost:8000"
TOKEN="YOUR_TEST_TOKEN"

# Test 1: Post list with is_liked
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/posts?limit=5" | \
  jq '.data[] | {id: .id, is_liked: .is_liked}'

# Test 2: Post detail with is_liked
POST_ID="test-post-id"
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/posts/$POST_ID" | \
  jq '.data | {id: .id, is_liked: .is_liked}'

# Test 3: Batch follow status
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": ["user-1", "user-2"]}' \
  "$BACKEND_URL/api/v1/follows/status" | \
  jq '.data'

# Test 4: Notification unread count
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/notifications/unread-count" | \
  jq '.data.unread_count'
```

#### Step 3.2: Frontend Smoke Tests

Using WeChat DevTools or test device:

```
Test Checklist:
□ Login works
□ Square page loads with like status
□ Like button shows correct state
□ Follow button appears for other users' posts
□ Follow button does NOT appear for own posts
□ Post detail shows correct like status
□ Follow button works in post detail
□ Notification badge shows in footer
□ Notification badge shows in profile
□ Unread count updates every 30 seconds
□ Clicking notification tab navigates to list
□ Notification list refreshes on show
□ Like/unlike updates UI immediately
□ Follow/unfollow updates UI immediately
□ Anonymous users see is_liked=false
```

### Phase 4: Monitoring Setup

#### Step 4.1: Backend Monitoring

```bash
# Monitor backend logs
tail -f /var/log/payday/backend.log

# Monitor error logs
tail -f /var/log/payday/error.log | grep -i error

# Monitor API response times (if using APM)
# Check your APM dashboard for:
# - /api/v1/posts endpoint latency
# - /api/v1/follows/status endpoint latency
# - Error rates (< 0.1% expected)
# - Cache hit rates (> 90% expected)
```

#### Step 4.2: Redis Monitoring

```bash
# Monitor Redis cache performance
redis-cli INFO stats

# Check cache hit rate
redis-cli INFO stats | grep keyspace_hits

# Monitor like status cache
redis-cli KEYS "like:status:*"

# Monitor follow cache (if applicable)
redis-cli KEYS "follow:*"
```

#### Step 4.3: Frontend Monitoring

Monitor using WeChat MP Platform Analytics:
```
Metrics to watch:
1. Page load times (square, post-detail, notification)
2. API error rates
3. User engagement (likes, follows, notification clicks)
4. Crash-free user rate (> 99% expected)
```

### Phase 5: Rollback Procedures

#### Backend Rollback

**Option A: Git Revert**

```bash
cd /Users/a1234/Documents/workspace/payDay

# Find the commit before enhancement
git log --oneline -20

# Reset to previous commit
git reset --hard <PRE_COMMIT_HASH>

# Restart backend service
sudo systemctl restart payday-backend

# Verify rollback
curl http://localhost:8000/api/v1/health
```

**Option B: Git Revert (preserves history)**

```bash
cd /Users/a1234/Documents/workspace/payDay

# Revert the enhancement commits
git revert --no-commit <FIRST_ENHANCEMENT_COMMIT>..<LAST_ENHANCEMENT_COMMIT>

# Commit the revert
git commit -m "rollback: revert like/follow/notification enhancements"

# Restart backend service
sudo systemctl restart payday-backend
```

#### Frontend Rollback

**WeChat Mini-Program Rollback**:

1. Go to [WeChat MP Platform](https://mp.weixin.qq.com/)
2. Navigate to: Development → Development Management → Development Versions
3. Find the previous stable version (e.g., 1.1.0)
4. Click "Set as Experience Version" (for testing)
5. If approved, click "Submit for Review" for full rollback

**Emergency Rollback** (if critical bug):

```bash
# Revert to previous working commit
cd miniapp
git reset --hard <PREVIOUS_STABLE_COMMIT>

# Rebuild
npm run build:mp-weixin

# Upload to WeChat as hotfix
# Version: 1.2.1-hotfix
```

## Verification Commands

### Post-Deployment Verification

```bash
# 1. Verify backend is running
curl -f http://localhost:8000/api/v1/health || echo "❌ Backend down"

# 2. Verify Redis is accessible
redis-cli ping || echo "❌ Redis down"

# 3. Verify MySQL is accessible
mysql -u root -p -e "SELECT 1;" || echo "❌ MySQL down"

# 4. Check backend logs for errors
tail -100 /var/log/payday/backend.log | grep -i error || echo "✅ No errors"

# 5. Verify new endpoints work
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": ["test"]}' \
  http://localhost:8000/api/v1/follows/status | jq '.code' | grep -q 0 && \
  echo "✅ Batch follow status endpoint works" || \
  echo "❌ Batch follow status endpoint failed"

# 6. Check cache is working
redis-cli --scan --pattern "like:status:*" | wc -l | grep -q 0 || \
  echo "✅ Cache is populated" || \
  echo "⚠️  Cache empty (expected if no activity yet)"
```

## Performance Benchmarks

### Expected Performance

#### Backend Endpoints
- `GET /api/v1/posts`: < 200ms (with like status)
- `GET /api/v1/posts/{id}`: < 100ms (with like status)
- `POST /api/v1/follows/status`: < 150ms (50 user IDs)
- `GET /api/v1/notifications/unread-count`: < 50ms

#### Cache Performance
- Like status cache hit rate: > 90%
- Follow status cache hit rate: > 85%
- Average cache response time: < 5ms

#### Frontend Performance
- Square page load: < 1.5s
- Post detail load: < 1s
- Notification list load: < 1s
- Unread count update: 30s polling interval

### Load Testing

```bash
# Install k6 or use similar tool
# Create load test script

# Test post list endpoint
k6 run --vus 100 --duration 30s - <<EOF
import http from 'k6/http';

export default function () {
  const url = 'http://localhost:8000/api/v1/posts?limit=20';
  const params = {
    headers: { 'Authorization': 'Bearer YOUR_TOKEN' },
  };
  http.get(url, params);
}
EOF

# Expected:
# - p95 latency < 500ms
# - Error rate < 1%
# - No 5xx errors
```

## Troubleshooting

### Common Issues

#### Issue 1: `is_liked` Field Always `false`

**Symptoms**: Authenticated users see all posts with `is_liked: false`

**Diagnosis**:
```bash
# Check if like cache exists
redis-cli KEYS "like:status:*"

# Check if user has liked anything
mysql -u root -p payday_db -e \
  "SELECT * FROM likes WHERE user_id='USER_ID' LIMIT 5;"
```

**Solutions**:
1. If cache missing: Warm up cache by liking a post
2. If DB empty: User hasn't liked anything - expected behavior
3. If cache exists but not returned: Check backend logs for errors

#### Issue 2: Follow Status Not Updating

**Symptoms**: Follow button doesn't change after follow/unfollow

**Diagnosis**:
```bash
# Check batch follow status endpoint
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": ["TARGET_USER_ID"]}' \
  http://localhost:8000/api/v1/follows/status

# Check if follow record exists
mysql -u root -p payday_db -e \
  "SELECT * FROM follows WHERE follower_id='USER_ID' AND following_id='TARGET_USER_ID';"
```

**Solutions**:
1. Frontend state not updated: Refresh page
2. API returning wrong status: Check backend logs
3. Database inconsistency: Verify follow record exists

#### Issue 3: Notification Badge Not Showing

**Symptoms**: No unread count badge in AppFooter or profile

**Diagnosis**:
```bash
# Check unread count endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/notifications/unread-count

# Check if notifications exist
mysql -u root -p payday_db -e \
  "SELECT COUNT(*) FROM notifications WHERE user_id='USER_ID' AND is_read=0;"
```

**Solutions**:
1. No unread notifications: Expected behavior
2. API error: Check backend logs
3. Composable not polling: Check browser console for errors

#### Issue 4: High Memory Usage

**Symptoms**: Backend service using excessive memory

**Diagnosis**:
```bash
# Check memory usage
ps aux | grep uvicorn

# Check Redis memory
redis-cli INFO memory | grep used_memory_human

# Check cache size
redis-cli --scan --pattern "like:status:*" | wc -l
```

**Solutions**:
1. Reduce cache TTL (currently 7 days for likes)
2. Implement cache eviction policy
3. Scale horizontally (add more workers)

### Log Analysis

```bash
# Search for errors in logs
grep -i error /var/log/payday/backend.log | tail -50

# Search for slow queries
grep "duration" /var/log/payday/backend.log | awk '$3 > 1000'

# Monitor like status cache operations
grep "is_liked" /var/log/payday/backend.log | tail -20

# Monitor follow status API
grep "/follows/status" /var/log/payday/backend.log | tail -20
```

## Post-Deployment Tasks

### 1. Update Documentation

```bash
# Update version number in CLAUDE.md
# Add new features to feature list

# Update API documentation
# Document new is_liked field
# Document new batch follow status endpoint
```

### 2. Monitor for 24-48 Hours

```bash
# Set up log monitoring
tail -f /var/log/payday/backend.log | grep -i error

# Check key metrics every few hours:
# - Error rate
# - Response time
# - Cache hit rate
# - User engagement (likes, follows, notifications)
```

### 3. Gather User Feedback

```
Channels to monitor:
1. WeChat mini-program feedback
2. App reviews
3. Customer support tickets
4. Social media mentions

Key questions:
- Is like status showing correctly?
- Are follow buttons easy to use?
- Are notifications timely?
- Any performance issues?
```

### 4. Create Hotfix Plan (If Needed)

```bash
# Document any issues found
# Create hotfix branch if needed
git checkout -b hotfix/issue-name

# Test and deploy hotfix
# Follow same deployment process
```

## Support Contacts

### Technical Support
- **Backend Lead**: [Contact info]
- **Frontend Lead**: [Contact info]
- **DevOps**: [Contact info]

### Emergency Contacts
- **On-Call Engineer**: [Contact info]
- **Product Manager**: [Contact info]

## Deployment Checklist

Use this checklist to ensure all steps are completed:

### Pre-Deployment
- [ ] All tests passing locally (150 backend, 107 frontend)
- [ ] Database backup completed
- [ ] Code backup tagged
- [ ] Dependencies verified
- [ ] Environment variables checked
- [ ] Rollback plan documented

### Backend Deployment
- [ ] Latest code pulled
- [ ] Dependencies installed
- [ ] Tests passed
- [ ] Linting passed
- [ ] Service restarted
- [ ] Health check passed
- [ ] New endpoints verified

### Frontend Deployment
- [ ] Latest code pulled
- [ ] Dependencies installed
- [ ] Tests passed
- [ ] Type check passed
- [ ] Linting passed
- [ ] Build completed
- [ ] Uploaded to WeChat
- [ ] Submitted for review
- [ ] Tested in DevTools

### Post-Deployment
- [ ] Smoke tests passed
- [ ] Monitoring configured
- [ ] Logs checked for errors
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Team notified
- [ ] User feedback channels open

## Success Criteria

Deployment is considered successful when:

1. ✅ All tests passing (257/257)
2. ✅ Backend health check returns 200
3. ✅ Frontend build completes without errors
4. ✅ New endpoints respond correctly
5. ✅ Cache is being populated
6. ✅ No errors in logs for 1 hour
7. ✅ Performance benchmarks met
8. ✅ WeChat review approved

## Conclusion

This deployment guide provides a comprehensive, step-by-step process for deploying the like status, follow buttons, and notification enhancements. Follow each step carefully, verify at each phase, and be prepared to rollback if issues arise.

**Estimated Deployment Time**: 2-3 hours (including WeChat review wait time)

**Rollback Time**: < 15 minutes

**Risk Level**: Low (backward compatible, no database migrations)

Good luck with the deployment! 🚀
