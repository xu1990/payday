# Admin Panel Router Documentation

## Overview

This document provides comprehensive documentation for all admin panel routes, including paths, components, access requirements, and navigation structure.

## Router Structure

The admin panel uses Vue Router with hash-based navigation. All routes require admin authentication except for the login page.

### Base Configuration
- **History Mode**: Hash (`createWebHashHistory`)
- **Base Path**: `/`
- **Authentication Required**: All routes except `/login`
- **Admin Scope Required**: All protected routes require `admin` scope in JWT token

---

## Routes Breakdown

### Authentication Routes

#### `/login` - Login Page
- **Component**: `Login.vue`
- **Meta**: `{ public: true }`
- **Access**: Public (no authentication required)
- **Purpose**: Admin login authentication
- **Navigation**: Automatically redirects to `/` if already logged in

### Main Layout Routes

All routes under `/` are wrapped in `Layout.vue` component and require authentication.

#### Root Redirect
- **Path**: `/`
- **Behavior**: Automatically redirects to `/statistics`

---

## Core Admin Routes

### Statistics and Analytics

#### `/statistics` - Dashboard
- **Component**: `Statistics.vue`
- **Access**: Admin required
- **Purpose**: Main admin dashboard with key metrics and analytics
- **Navigation**: Default landing page after login

### User Management

#### `/users` - User List
- **Component**: `UserList.vue`
- **Access**: Admin required
- **Purpose**: List and manage all system users
- **Features**: Search, filter, user management

#### `/users/:id` - User Detail
- **Component**: `UserDetail.vue`
- **Access**: Admin required
- **Purpose**: View and edit individual user details
- **Features**: User profile, activity history, permissions

#### `/user-addresses` - User Addresses
- **Component**: `UserAddresses.vue`
- **Access**: Admin required
- **Purpose**: View and manage user delivery addresses
- **Features**: Search, edit, validate addresses
- **API**: `/api/v1/admin/user-addresses`

### Salary and Financial Data

#### `/salary-records` - Salary Records
- **Component**: `SalaryList.vue`
- **Access**: Admin required
- **Purpose**: Manage user salary records
- **Features**: View, edit, filter salary data

### Content Management

#### `/posts` - Community Posts
- **Component**: `PostList.vue`
- **Access**: Admin required
- **Purpose**: Manage community posts
- **Features**: Review, approve, delete posts

#### `/comments` - Comments
- **Component**: `CommentList.vue`
- **Access**: Admin required
- **Purpose**: Manage user comments
- **Features**: Moderate, filter comments

#### `/risk-pending` - Risk Management
- **Component**: `RiskPending.vue`
- **Access**: Admin required
- **Purpose**: Handle content risk detection
- **Features**: Review flagged content, make decisions

#### `/topics` - Topics Management
- **Component**: `topics/index.vue`
- **Access**: Admin required
- **Purpose**: Manage discussion topics
- **Features**: Create, edit, organize topics

### Membership and Products

#### `/memberships` - Membership Management
- **Component**: `Membership.vue`
- **Access**: Admin required
- **Purpose**: Manage membership plans
- **Features**: Create, update, manage memberships

#### `/themes` - Theme Management
- **Component**: `Theme.vue`
- **Access**: Admin required
- **Purpose**: Manage app themes and configurations
- **Features**: Create, update themes

#### `/orders` - Order Management
- **Component**: `Order.vue`
- **Access**: Admin required
- **Purpose**: Manage user orders
- **Features**: View, update order status

### Mini-program Configuration

#### `/miniprogram` - Mini-program Settings
- **Component**: `MiniprogramConfig.vue`
- **Access**: Admin required
- **Purpose**: Configure mini-program settings
- **Features**: General mini-program configuration

#### `/splash` - Splash Settings
- **Component**: `SplashSettings.vue`
- **Access**: Admin required
- **Purpose**: Configure splash screen
- **Features**: Upload and manage splash screen images

#### `/agreements` - Agreement Management
- **Component**: `AgreementManagement.vue`
- **Access**: Admin required
- **Purpose**: Manage user agreements and policies
- **Features**: Create, update legal documents

### Feedback and Support

#### `/feedback` - User Feedback
- **Component**: `FeedbackList.vue`
- **Access**: Admin required
- **Purpose**: Manage user feedback and support requests
- **Features**: View, respond to feedback

---

## Point Shop Routes

### Point Shop Management

#### `/point-shop` - Product Management
- **Component**: `PointShop.vue`
- **Access**: Admin required
- **Purpose**: Manage point shop products
- **Features**:
  - Create/update products
  - SKU management for multi-variant products
  - Inventory management
  - Product status control
- **API**: `/api/v1/admin/point-products`

#### `/point-categories` - Category Management
- **Component**: `PointCategories.vue`
- **Access**: Admin required
- **Purpose**: Manage product categories
- **Features**:
  - Hierarchical category structure (3 levels)
  - Category icons and banners
  - Category tree navigation
  - Drag-and-drop sorting
- **API**: `/api/v1/admin/point-categories`

### Order Fulfillment

#### `/point-orders` - Point Orders
- **Component**: `PointOrders.vue`
- **Access**: Admin required
- **Purpose**: Manage point shop orders
- **Features**:
  - View order details
  - Update order status
  - Process payments/refunds
- **API**: `/api/v1/admin/point-orders`

#### `/point-shipments` - Shipment Management
- **Component**: `PointShipments.vue`
- **Access**: Admin required
- **Purpose**: Manage order shipments
- **Features**:
  - Process shipments
  - Track delivery status
  - Bulk shipment operations
- **API**: `/api/v1/admin/point-shipments`

#### `/point-returns` - Return Management
- **Component**: `PointReturns.vue`
- **Access**: Admin required
- **Purpose**: Process return requests
- **Features**:
  - Review return requests
  - Approve/reject returns
  - Process refunds
  - Update inventory
- **API**: `/api/v1/admin/point-returns`

### Shipping Configuration

#### `/couriers` - Courier Management
- **Component**: `Couriers.vue`
- **Access**: Admin required
- **Purpose**: Manage shipping companies
- **Features**:
  - Add/remove couriers
  - Configure tracking URLs
  - Manage courier contacts
- **API**: `/api/v1/admin/couriers`

#### `/shipping-templates` - Shipping Templates
- **Component**: `ShippingTemplates.vue`
- **Access**: Admin required
- **Purpose**: Configure shipping costs
- **Features**:
  - Create shipping templates
  - Set regional pricing
  - Configure shipping rules
- **API**: `/api/v1/admin/shipping-templates`

---

## Navigation Menu Structure

The admin panel menu is organized by functional areas:

### Main Menu Groups

1. **数据统计** (Statistics)
   - `statistics` - Dashboard

2. **用户管理** (User Management)
   - `users` - User List
   - `user-addresses` - User Addresses
   - `salary-records` - Salary Records

3. **内容管理** (Content Management)
   - `posts` - Community Posts
   - `comments` - Comments
   - `risk-pending` - Risk Management
   - `topics` - Topics
   - `feedback` - User Feedback

4. **商城管理** (Point Shop)
   - `point-shop` - Products
   - `point-categories` - Categories
   - `point-orders` - Orders
   - `point-shipments` - Shipments
   - `point-returns` - Returns
   - `couriers` - Couriers
   - `shipping-templates` - Shipping

5. **系统配置** (System Configuration)
   - `memberships` - Memberships
   - `themes` - Themes
   - `orders` - Orders
   - `miniprogram` - Mini-program
   - `splash` - Splash
   - `agreements` - Agreements

---

## Access Control

### Authentication Flow

1. **Route Navigation**: User attempts to access protected route
2. **Authentication Check**: Router middleware checks `requiresAuth` meta
3. **Login Redirect**: If not logged in, redirect to `/login`
4. **Scope Validation**: If logged in, check for `admin` scope in JWT token
5. **Access Granted/Denied**: Redirect to login if scope missing

### JWT Token Requirements

All admin routes require JWT token with:
- `sub`: Admin user ID
- `scope: "admin"`: Admin permission scope
- `exp`: Valid expiration time

### Error Handling

- **401 Unauthorized**: Redirect to login
- **403 Forbidden**: Scope missing (auto logout)
- **404 Not Found**: Invalid route

---

## Route Development Guidelines

### Adding New Routes

1. **Component Creation**: Create Vue component in `src/views/`
2. **Route Registration**: Add route in `src/router/index.ts`
3. **Meta Configuration**: Set `requiresAuth: true` for protected routes
4. **Menu Integration**: Add to navigation menu (if applicable)
5. **API Integration**: Create corresponding API endpoints

### Best Practices

1. **Consistent Naming**: Use kebab-case for route paths
2. **Component Organization**: Group related components in folders
3. **Lazy Loading**: All components use lazy loading with `import()`
4. **Meta Tags**: Use meta for route-level information
5. **Navigation**: Follow established menu hierarchy

### Security Considerations

1. **Always require admin scope** for admin routes
2. **Validate JWT tokens** on every protected route
3. **Implement proper error handling**
4. **Log access attempts** for security monitoring

---

## Route Reference

### All Routes Summary

| Path | Component | Access | Purpose |
|------|-----------|--------|---------|
| `/login` | Login.vue | Public | Admin login |
| `/` | Layout.vue | Admin | Main layout |
| `/statistics` | Statistics.vue | Admin | Dashboard |
| `/users` | UserList.vue | Admin | User management |
| `/users/:id` | UserDetail.vue | Admin | User details |
| `/user-addresses` | UserAddresses.vue | Admin | Address management |
| `/salary-records` | SalaryList.vue | Admin | Salary records |
| `/posts` | PostList.vue | Admin | Post management |
| `/comments` | CommentList.vue | Admin | Comment moderation |
| `/risk-pending` | RiskPending.vue | Admin | Risk management |
| `/topics` | topics/index.vue | Admin | Topics management |
| `/memberships` | Membership.vue | Admin | Membership management |
| `/themes` | Theme.vue | Admin | Theme management |
| `/orders` | Order.vue | Admin | Order management |
| `/miniprogram` | MiniprogramConfig.vue | Admin | Mini-program config |
| `/splash` | SplashSettings.vue | Admin | Splash screen |
| `/agreements` | AgreementManagement.vue | Admin | Agreement management |
| `/feedback` | FeedbackList.vue | Admin | Feedback management |
| `/point-shop` | PointShop.vue | Admin | Product management |
| `/point-categories` | PointCategories.vue | Admin | Category management |
| `/point-orders` | PointOrders.vue | Admin | Point orders |
| `/point-shipments` | PointShipments.vue | Admin | Shipment management |
| `/point-returns` | PointReturns.vue | Admin | Return management |
| `/couriers` | Couriers.vue | Admin | Courier management |
| `/shipping-templates` | ShippingTemplates.vue | Admin | Shipping templates |

### Navigation Integration

Routes are automatically integrated into the navigation menu based on their functional group. The menu structure follows the Chinese naming convention to match the admin interface design.