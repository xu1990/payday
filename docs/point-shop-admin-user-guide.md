# Point Shop Admin User Guide

## Table of Contents
- [Section 1: Introduction](#section-1-introduction)
- [Section 2: Category Management](#section-2-category-management)
- [Section 3: Product Management](#section-3-product-management)
- [Section 4: Shipping Configuration](#section-4-shipping-configuration)
- [Section 5: Order Fulfillment](#section-5-order-fulfillment)
- [Section 6: User Management](#section-6-user-management)

---

## Section 1: Introduction

### Purpose of the Point Shop Admin Module

The Point Shop Admin Module provides a comprehensive interface for managing all aspects of the points-based e-commerce system. This allows administrators to manage products, categories, shipping, orders, and customer interactions effectively.

### Overview of Features

The admin module consists of seven main sections:

1. **Category Management** - Organize products into hierarchical categories with up to 3 levels
2. **Courier Management** - Manage shipping service providers
3. **User Addresses** - View and manage user delivery addresses
4. **Point Shop** - Manage products with advanced SKU support
5. **Shipping Templates** - Configure regional shipping costs
6. **Point Shipments** - Track and manage order shipments
7. **Point Returns** - Process customer return requests

---

## Section 2: Category Management

### Accessing Category Management

Navigate to `/admin/point-categories` to access the category management interface.

### Creating Categories

1. Click the "Add Category" button in the top-right corner
2. Fill in the required information:
   - **Name**: Category name (max 50 characters)
   - **Description**: Optional category description
   - **Level**: Select the level (1, 2, or 3)
   - **Parent Category**: Required for levels 2 and 3
   - **Icon**: Upload a category icon image (recommended: 32x32 pixels)
   - **Banner**: Upload a category banner image (recommended: 800x300 pixels)
3. Click "Submit" to save

### Building Category Hierarchy

The system supports up to 3 levels of categories:

- **Level 1**: Root categories (e.g., "Electronics", "Clothing")
- **Level 2**: Subcategories of Level 1 (e.g., "Smartphones", "Laptops" under "Electronics")
- **Level 3**: Subcategories of Level 2 (e.g., "iPhone", "Samsung" under "Smartphones")

**Best Practices**:
- Keep Level 1 categories broad and general
- Use Level 2 for more specific product types
- Use Level 3 for specific brands or variations
- Limit Level 1 to 10-15 categories maximum
- Ensure each level has a clear purpose

### Managing Icons and Banners

**Icon Guidelines**:
- Size: 32x32 pixels (square)
- Format: PNG or JPG
- File size: Max 50KB
- Use simple, recognizable icons
- Ensure good contrast and visibility

**Banner Guidelines**:
- Size: 800x300 pixels (16:9 aspect ratio recommended)
- Format: PNG or JPG
- File size: Max 2MB
- Use high-quality, relevant imagery
- Include category name prominently

### Editing Categories

1. Click the "Edit" button on the desired category
2. Modify any field except the level and parent relationship
3. Click "Submit" to save changes

### Deleting Categories

1. Click the "Delete" button on the desired category
2. Confirm the deletion
3. **Note**: You cannot delete categories that have products or subcategories

---

## Section 3: Product Management

### Accessing Product Management

Navigate to `/admin/point-shop` to access the product management interface.

### Creating Simple Products (No SKU)

1. Click "Add Product"
2. Fill in the product information:
   - **Name**: Product name (max 100 characters)
   - **Description**: Detailed product description
   - **Category**: Select the appropriate category
   - **Image**: Upload product images (up to 10)
   - **Points Required**: Number of points required
   - **Stock Quantity**: Available inventory
   - **Status**: Active/Inactive
3. Click "Submit" to create the product

### Creating Products with SKU Support

For products with multiple variants (e.g., different colors, sizes):

1. Click "Add Product"
2. Fill in basic product information as above
3. Enable "Has SKU" option
4. **Add Specifications**:
   - Click "Add Specification"
   - Enter specification name (e.g., "Color", "Size")
   - Add values (e.g., "Red, Blue, Green" or "S, M, L")
5. **Generate SKU Combinations**:
   - Click "Generate SKUs"
   - The system will automatically create all combinations
6. **Configure Each SKU**:
   - Set points required for each variant
   - Set stock quantity for each variant
   - Upload variant-specific images if needed
7. Click "Submit"

### Managing SKU Combinations

The system automatically generates SKU combinations based on specification values:

**Example**: Color (Red, Blue) + Size (S, M, L)
- Red-S, Red-M, Red-L
- Blue-S, Blue-M, Blue-L

**SKU Management Tips**:
- Use clear specification names
- Group related values together
- Consider stock management across variants
- Update points for each variant separately
- Use variant images when available

### Inventory Management

- **Stock Tracking**: Each SKU has independent inventory
- **Stock Alerts**: Set minimum stock levels for notifications
- **Batch Updates**: Use bulk operations for inventory adjustments
- **Stock History**: View stock change history

### Product Status Management

- **Active**: Product visible and available for purchase
- **Inactive**: Product hidden from users but data preserved
- **Out of Stock**: Available in catalog but shows stock status
- **Discontinued**: Product removed from catalog

---

## Section 4: Shipping Configuration

### Managing Couriers

Navigate to `/admin/couriers` to manage shipping service providers.

#### Adding a Courier

1. Click "Add Courier"
2. Fill in the information:
   - **Name**: Courier company name
   - **Code**: Internal code (e.g., "SF", "JD")
   - **Tracking URL**: Template URL for tracking (use `{tracking_number}` placeholder)
   - **Contact**: Company contact information
3. Click "Submit"

#### Example Tracking URL Templates:
- SF Express: `https://www.sf-express.com/cn/sc/service-availability?number={tracking_number}`
- JD Logistics: `https://www.jd.com/help/question-103764.html?trackingNumber={tracking_number}`
- SF Standard: `https://tracking.sfbest.com/number/{tracking_number}`

### Setting Up Shipping Templates

Navigate to `/admin/shipping-templates` to configure shipping costs.

#### Creating Shipping Templates

1. Click "Add Template"
2. Enter template name and description
3. Add regional pricing:
   - **Select Region**: Choose province/city
   - **Base Price**: Standard shipping cost
   - **Additional Rules**: Weight surcharges, remote area fees
4. Set default template for new orders
5. Click "Submit"

#### Regional Pricing Configuration

**Coverage Levels**:
- National: Covers all regions
- Province-level: Specific provinces
- City-level: Specific cities
- District-level: Specific districts

**Pricing Strategy**:
- Set competitive base rates
- Consider rural/remote surcharges
- Free shipping thresholds (if applicable)
- Bulk order discounts

### Shipping Workflow

1. **Customer Checkout**: Customer selects delivery address
2. **Template Matching**: System applies appropriate shipping template
3. **Cost Calculation**: Final shipping cost calculated
4. **Order Processing**: Shipping cost included in order total
5. **Courier Assignment**: Courier selected for delivery

---

## Section 5: Order Fulfillment

### Processing Shipments

Navigate to `/admin/point-shipments` to manage order shipments.

#### Processing Steps

1. **Select Orders**: Choose pending orders for shipment
2. **Assign Courier**: Select shipping company
3. **Generate Tracking Number**: Create tracking number
4. **Update Order Status**: Mark orders as shipped
5. **Notify Customer**: Send shipment notification

#### Bulk Shipment Processing

1. Select multiple orders using checkboxes
2. Click "Process Shipment"
3. Assign courier and tracking number
4. Confirm shipment
5. System updates all selected orders

### Tracking Delivery

**Shipment Status**:
- **Pending**: Order confirmed, awaiting shipment
- **Shipped**: Package with courier
- **In Transit**: Package in transit
- **Delivered**: Package delivered to customer
- **Exception**: Delivery issue encountered

**Tracking Features**:
- Real-time status updates
- Automated status sync with couriers
- Exception handling and alerts
- Delivery confirmation

### Handling Returns

Navigate to `/admin/point-returns` to process customer returns.

#### Return Request Processing

1. **Review Request**: Customer details, reason, photos
2. **Validate Return**: Check return eligibility
3. **Approve/Reject**: Make decision
4. **Process Refund**: Return points to customer account
5. **Update Inventory**: Update product stock
6. **Close Request**: Mark return as complete

#### Return Status Workflow

- **Pending**: New return request
- **Approved**: Return approved
- **Rejected**: Return rejected
- **In Transit**: Return package being shipped back
- **Received**: Return package received
- **Completed**: Return fully processed

**Return Processing Guidelines**:
- Process requests within 24-48 hours
- Communicate clearly with customers
- Document all interactions
- Use photos for damage verification
- Update inventory promptly

---

## Section 6: User Management

### Viewing User Addresses

Navigate to `/admin/user-addresses` to view and manage customer addresses.

#### Address Management Features

- **Search**: Filter addresses by user name, phone, or address
- **View Details**: Complete address information
- **Edit**: Update address information (user can also edit)
- **Set Default**: Mark as default address for user
- **Delete**: Remove outdated addresses

#### Address Quality Control

**Common Issues to Monitor**:
- Incomplete addresses (missing province/city/district)
- Invalid phone numbers
- Duplicate addresses
- High-risk areas (if applicable)

**Best Practices**:
- Regular data cleanup
- Encourage users to keep addresses current
- Validate addresses before shipping
- Provide address verification system

### Managing Address Issues

1. **Identify Problems**: Review address for completeness
2. **Contact User**: Send verification message
3. **Update Address**: Edit if necessary
4. **Document**: Keep records of changes
5. **Monitor**: Check for recurring issues

### Communication Guidelines

- **Proactive**: Notify users about shipping updates
- **Clear**: Use simple, direct language
- **Timely**: Respond promptly to customer inquiries
- **Professional**: Maintain consistent tone
- **Helpful**: Provide detailed information when needed

### Performance Metrics

Track these metrics for optimal operations:

- **Order Processing Time**: Time from order to shipment
- **Delivery Success Rate**: Percentage of successful deliveries
- **Return Rate**: Percentage of orders returned
- **Customer Satisfaction**: User feedback and ratings
- **Inventory Accuracy**: Stock level accuracy

---

## Quick Reference

### Common Tasks

| Task | Location | Key Steps |
|------|----------|-----------|
| Add Product Point Shop | `/admin/point-shop` | Fill product details, set SKU if needed |
| Update Category | `/admin/point-categories` | Edit icon, banner, or info |
| Process Orders | `/admin/point-shipments` | Assign courier, generate tracking |
| Handle Returns | `/admin/point-returns` | Review, approve/refund, update inventory |
| Check Addresses | `/admin/user-addresses` | Search, verify, update if needed |

### Important Notes

- Always run database migrations after making model changes
- Use appropriate HTTP status codes for API responses
- Validate all user inputs before processing
- Log all important actions for audit trail
- Keep customer data secure and private

### Troubleshooting

**Common Issues**:
- SKU generation fails - Check specification values
- Shipping calculation error - Verify template configuration
- Address lookup fails - Check regional data
- Return processing stuck - Ensure all required fields

**Support**:
- Contact technical support for system issues
- Refer to API documentation for integration problems
- Check logs for debugging information