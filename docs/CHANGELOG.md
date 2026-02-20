# PayDay Mini-Program - Changelog

## Version 1.2.0 - Like Status, Follow Buttons, and Notifications (2026-02-20)

### 🎉 Major New Features

#### 1. Like Status Display
- **Square Page**: Each post now shows whether you've liked it
- **Post Detail**: Like button displays your current like status
- **Real-Time Updates**: Like status updates immediately when you like/unlike

**User Impact**: You can now instantly see which posts you've liked without having to tap the like button to check.

---

#### 2. Follow Buttons for Post Authors
- **Square Page**: Follow button added to each post card
- **Post Detail**: Follow button next to author name
- **Smart Display**: Follow button only shows for other users' posts (not your own)
- **Batch Status**: Efficiently checks follow status for multiple authors at once

**User Impact**: Easily follow interesting authors directly from the square or post detail pages with a single tap.

---

#### 3. Real-Time Notification Updates
- **Footer Notification Tab**: New bell icon in main navigation bar
- **Unread Count Badge**: Red badge shows number of unread notifications (caps at 99+)
- **Auto-Refresh**: Notifications update every 30 seconds automatically
- **On-Screen Refresh**: Notification list refreshes when you switch to it

**User Impact**: Never miss important updates! The notification badge keeps you informed of new likes, comments, and follows in real-time.

---

#### 4. Follow Notifications
- **New Notification Type**: Get notified when someone follows you
- **Follower Info**: See who followed you
- **Notification List**: All your follows appear in your notification list

**User Impact**: Know immediately when someone new follows you, helping you grow your community.

---

### 🐛 Bug Fixes

#### Fixed: Like Status Not Showing in Square
- **Issue**: Square page didn't show which posts you'd liked
- **Fix**: Backend now includes `is_liked` field in post list response
- **Result**: Like status is accurate and instant

---

#### Fixed: Post Detail Always Showed "Not Liked"
- **Issue**: Post detail page initialized like status as false, ignoring your actual likes
- **Fix**: Post detail now uses server-provided like status
- **Result**: Like button shows correct state when you open a post

---

#### Fixed: No Easy Way to Follow Post Authors
- **Issue**: Had to visit user's profile to follow them
- **Fix**: Follow button now appears directly in square and post detail pages
- **Result**: Follow authors with one tap, no profile visit needed

---

#### Fixed: Notification Badge Not Updating
- **Issue**: Unread count didn't update unless you refreshed the page
- **Fix**: Added automatic polling every 30 seconds + on-screen refresh
- **Result**: Notification count stays up-to-date automatically

---

### ⚡ Performance Improvements

#### Faster Like Status Checking
- **Before**: Client-side tracking required extra API calls
- **After**: Like status included in post response (cached for 7 days)
- **Impact**: Faster page loads, fewer API calls

---

#### Efficient Follow Status Batching
- **Before**: Each follow button required separate API call
- **After**: Single API call checks up to 50 authors at once
- **Impact**: Square page loads faster with many posts

---

#### Optimized Notification Polling
- **Interval**: 30 seconds (balances real-time vs. battery)
- **Smart Refresh**: Only polls when app is active
- **Impact**: Real-time updates without draining battery

---

### 🎨 UI/UX Improvements

#### Square Page
- Post cards now show like status with filled/empty heart icon
- Follow button appears next to author name (small, unobtrusive)
- Follow button hidden for your own posts

#### Post Detail Page
- Like button shows correct state immediately (no animation glitch)
- Follow button positioned next to author name for easy access
- Consistent styling with rest of app

#### Notification Tab
- Bell icon in footer navigation (between "Square" and "Profile")
- Red badge with number (99+ if over 99)
- Smooth animations when count changes

#### Profile Page
- Notification icon in header matches footer
- Unread count shows in both places
- Tapping either icon goes to notification list

---

### 🔒 Privacy & Security

#### Anonymous Users
- Like status always shows as "not liked" (expected)
- Follow buttons hidden (require login)
- Notifications not accessible

#### Your Own Posts
- Follow button doesn't appear (can't follow yourself)
- Maintains clean UI without redundant buttons

#### Data Protection
- No personal information exposed
- Anonymous names used throughout
- Follow relationships are private

---

### 📱 Technical Details

#### Backend Changes
- **New API Field**: `is_liked` in post responses
- **New Endpoint**: `POST /api/v1/follows/status` (batch follow checking)
- **New Notification Type**: `follow` notifications
- **Performance**: Uses Redis cache for fast lookups

#### Frontend Changes
- **New Composable**: `useNotificationUnread` (handles polling)
- **Updated Components**: Square, PostDetail, AppFooter, NotificationList
- **Optimistic UI**: Like/follow actions update immediately, sync in background

---

### 🔄 How to Use

#### Viewing Like Status
1. Open square page
2. Each post shows filled heart ❤️ if you've liked it
3. Empty heart 🤍 if you haven't liked it
4. Tap heart to like/unlike (updates instantly)

#### Following Authors
1. Find a post from someone you don't follow
2. Look for "关注" button next to author name
3. Tap to follow (button changes to "已关注")
4. Tap "已关注" to unfollow

#### Checking Notifications
1. Look at bell icon 🔔 in footer navigation
2. Red badge shows unread count
3. Tap bell icon to go to notification list
4. Badge disappears when all notifications read

#### Follow Notifications
1. When someone follows you, you get a notification
2. Shows: "XXX 关注了你"
3. Tap notification to go to their profile
4. Follow back if you want!

---

### ⚠️ Known Limitations

#### Notification Polling
- **30-second delay**: Not instant (would require WebSocket)
- **Battery**: Polling uses minimal battery but not zero
- **Future**: We're working on push notifications for instant updates

#### Follow Status
- **Batch limit**: Checks up to 50 authors per page load
- **Refresh**: Status updates when you refresh or navigate
- **Real-time**: Changes appear after page reload

---

### 🐛 Troubleshooting

#### Like Status Not Showing
- **Solution**: Pull down to refresh the page
- **Cause**: Old data cached, refresh gets latest

#### Follow Button Missing
- **Check**: Are you logged in?
- **Check**: Is this your own post? (button hidden for own posts)
- **Solution**: Login to see follow buttons

#### Notification Badge Not Updating
- **Wait**: Up to 30 seconds for auto-refresh
- **Solution**: Switch to another tab and back (instant refresh)
- **Check**: Network connection must be active

---

### 📊 What's Coming Next

#### Future Enhancements (Planned)
- **Push Notifications**: Instant alerts for likes/comments/follows
- **Notification Preferences**: Choose which notifications to receive
- **Notification Categories**: Group by type (likes, comments, follows)
- **Suggested Users**: Who to follow based on your interests

---

### 💬 Feedback

We'd love to hear from you!

**How to Give Feedback**:
1. Go to Profile page
2. Tap "Settings" (gear icon)
3. Tap "Feedback"
4. Tell us what you think!

**What to Tell Us**:
- Do you like the new like status display?
- Are follow buttons easy to use?
- Are notifications helpful?
- Any bugs or issues?
- Ideas for improvements?

---

### 🙏 Thank You!

Thank you for using PayDay! This release makes it easier to connect with others and stay updated on your social activity.

**Version**: 1.2.0
**Release Date**: 2026-02-20
**Features**: 4 major features, 4 bug fixes, 3 performance improvements

Enjoy the updates! 🎉

---

## Version 1.1.0 - Previous Release

### Features
- User profiles
- Follow/unfollow users
- User stats (followers, following, posts)
- View user's posts

---

## Version 1.0.0 - Initial Release

### Features
- User registration and login
- Create and view posts
- Like and comment on posts
- Square page (hot/latest feeds)
- Notification system
- Payday tracking
- Salary sharing
