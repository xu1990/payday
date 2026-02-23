# User Avatar Feature - Manual Testing Guide

## Prerequisites
- Backend running on port 8000
- Miniapp dev server running
- Database with test data (9 posts already exist)

## Start Services

### Backend:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend:
```bash
cd miniapp
npm run dev
```

## Manual Test Checklist

### 1. Create New Post with Avatar
- [ ] Login to miniapp
- [ ] Navigate to square page
- [ ] Click "发帖" button
- [ ] Create a new post
- [ ] Verify: Post appears in list with your avatar

### 2. View Square List (Hot)
- [ ] Navigate to square page
- [ ] Switch to "热门" tab
- [ ] Verify: All posts show user avatars
- [ ] Verify: Posts without avatar show green placeholder with first letter

### 3. View Square List (Latest)
- [ ] Navigate to square page
- [ ] Switch to "最新" tab
- [ ] Verify: All posts show user avatars or placeholders

### 4. View Post Detail
- [ ] Click on any post in square list
- [ ] Verify: Post detail page shows author avatar
- [ ] Verify: Avatar size is medium (larger than list view)

### 5. View My Likes
- [ ] Navigate to "我的" page
- [ ] Go to "我的点赞"
- [ ] Verify: Liked posts show user avatars

### 6. Placeholder Fallback
- [ ] Find a post from user without avatar (if any)
- [ ] Verify: Shows green circle with first letter of anonymous_name

### 7. Avatar Loading
- [ ] Refresh square page
- [ ] Verify: Avatar images load correctly
- [ ] Verify: No broken image icons

## Expected Results

All posts display avatars correctly
Placeholder shown when avatar is null
No console errors related to avatar display
Avatar sizes appropriate (small: 60rpx, medium: 80rpx)

## Test Data Notes

Current database has 9 posts with avatars already populated from migration.
