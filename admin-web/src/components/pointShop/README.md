# Point Shop Shared Components

This directory contains reusable Vue 3 components for the Point Shop admin module.

## Components

### CategoryTreeSelect.vue

Category tree picker with hierarchical structure support.

**Features:**

- Single selection from category tree
- Auto-load categories from API
- Disabled inactive categories
- Clearable selection
- Lazy loading support

**Props:**

- `modelValue?: string | null` - Selected category ID
- `placeholder?: string` - Placeholder text (default: "请选择分类")
- `disabled?: boolean` - Disabled state
- `clearable?: boolean` - Allow clearing selection (default: true)
- `activeOnly?: boolean` - Show only active categories (default: true)

**Events:**

- `update:modelValue` - Emitted when selection changes

**Example:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { CategoryTreeSelect } from '@/components/pointShop'

const categoryId = ref<string | null>(null)
</script>

<template>
  <CategoryTreeSelect v-model="categoryId" placeholder="请选择商品分类" :disabled="false" />
</template>
```

---

### CourierSelect.vue

Courier company dropdown with feature tags.

**Features:**

- Searchable courier list
- Show courier features (COD, cold chain)
- Show courier codes optionally
- Filter by active status
- Auto-load from API

**Props:**

- `modelValue?: string | null` - Selected courier code
- `placeholder?: string` - Placeholder text (default: "请选择物流公司")
- `disabled?: boolean` - Disabled state
- `clearable?: boolean` - Allow clearing selection (default: true)
- `filterable?: boolean` - Enable search/filter (default: true)
- `activeOnly?: boolean` - Show only active couriers (default: true)
- `showCode?: boolean` - Display courier code in option (default: false)

**Events:**

- `update:modelValue` - Emitted when selection changes

**Example:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { CourierSelect } from '@/components/pointShop'

const courierCode = ref<string | null>(null)
</script>

<template>
  <CourierSelect
    v-model="courierCode"
    placeholder="请选择物流公司"
    :active-only="true"
    :show-code="true"
  />
</template>
```

---

### AddressForm.vue

Complete address input form with validation.

**Features:**

- Full address fields (contact, phone, region, detailed address, postal code)
- Built-in form validation
- Region cascader (province/city/district)
- Optional "set as default" switch
- Exposed validation methods

**Props:**

- `modelValue: AddressFormData | UserAddress` - Address data object
- `showDefault?: boolean` - Show "set as default" switch (default: false)
- `disabled?: boolean` - Disabled state

**Events:**

- `update:modelValue` - Emitted when form data changes
- `validate` - Emitted on field validation

**Exposed Methods:**

- `validate()` - Validate entire form, returns Promise<boolean>
- `resetFields()` - Reset form to initial state
- `clearValidate()` - Clear validation messages

**AddressFormData Interface:**

```typescript
interface AddressFormData {
  contact_name: string
  contact_phone: string
  province_code: string
  province_name: string
  city_code: string
  city_name: string
  district_code: string
  district_name: string
  detailed_address: string
  postal_code?: string
  is_default?: boolean
}
```

**Example:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { AddressForm, type AddressFormData } from '@/components/pointShop'

const addressFormRef = ref()
const addressData = ref<AddressFormData>({
  contact_name: '',
  contact_phone: '',
  province_code: '',
  province_name: '',
  city_code: '',
  city_name: '',
  district_code: '',
  district_name: '',
  detailed_address: '',
  postal_code: '',
})

async function handleSubmit() {
  const isValid = await addressFormRef.value.validate()
  if (isValid) {
    // Submit addressData.value
  }
}
</script>

<template>
  <AddressForm ref="addressFormRef" v-model="addressData" :show-default="true" />
</template>
```

---

### RegionPricingForm.vue

Shipping region configuration for pricing templates.

**Features:**

- Support for 3 charge types: free, flat rate, by region
- Multi-province selection for region pricing
- First piece / additional piece pricing
- Add/remove region configurations
- Integrated with el-table

**Props:**

- `modelValue: PricingConfig` - Pricing configuration object
- `chargeType: 'free' | 'flat' | 'by_region'` - Charge type
- `disabled?: boolean` - Disabled state

**Events:**

- `update:modelValue` - Emitted when config changes

**PricingConfig Interface:**

```typescript
interface RegionPricing {
  provinces: string[] // Province codes
  first_piece: number
  first_piece_fee: number
  additional_piece: number
  additional_piece_fee: number
}

interface PricingConfig {
  first_piece?: number // For free/flat
  flat_fee?: number // For flat
  region_pricing?: RegionPricing[] // For by_region
}
```

**Example:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { RegionPricingForm, type PricingConfig } from '@/components/pointShop'

const pricingConfig = ref<PricingConfig>({
  first_piece: 1,
  flat_fee: 0,
  region_pricing: [],
})

const chargeType = ref<'free' | 'flat' | 'by_region'>('by_region')
</script>

<template>
  <RegionPricingForm v-model="pricingConfig" :charge-type="chargeType" :disabled="false" />
</template>
```

---

## Usage in Existing Pages

### Updating PointShop.vue to use CategoryTreeSelect

```vue
<script setup lang="ts">
import { CategoryTreeSelect } from '@/components/pointShop'

// In the form dialog, replace el-select with:
<CategoryTreeSelect
  v-model="formData.category_id"
  placeholder="请选择商品分类"
  :disabled="isEdit"
/>
```

### Updating PointShipments.vue to use CourierSelect

```vue
<script setup lang="ts">
import { CourierSelect } from '@/components/pointShop'

// In the create/edit form, replace el-select with:
<CourierSelect
  v-model="formData.courier_code"
  placeholder="请选择物流公司"
  :active-only="true"
/>
```

### Updating UserAddresses.vue to use AddressForm

```vue
<script setup lang="ts">
import { AddressForm } from '@/components/pointShop'

// In the edit dialog, replace the form with:
<AddressForm
  ref="addressFormRef"
  v-model="formData"
  :show-default="true"
  @validate="handleValidate"
/>
```

---

## Type Exports

All component types are exported from `index.ts`:

```typescript
import {
  CategoryTreeSelect,
  CourierSelect,
  AddressForm,
  RegionPricingForm,
  type AddressFormData,
  type RegionPricing,
  type PricingConfig,
} from '@/components/pointShop'
```

---

## Development Notes

### Adding New Components

1. Create component `.vue` file in this directory
2. Follow Vue 3 Composition API patterns
3. Include JSDoc comments with features, props, events
4. Use TypeScript with proper type definitions
5. Export from `index.ts`

### Component Design Patterns

- **Props Interface**: Define clear interface with defaults
- **Emits**: Use TypeScript emit definitions
- **State Management**: Use local ref with watch for two-way binding
- **Loading States**: Show loading indicators during API calls
- **Error Handling**: Use ElMessage for user feedback
- **Accessibility**: Include aria-labels where appropriate
- **Styling**: Scoped styles, follow Element Plus patterns

### Testing

Test components in isolation before integrating:

```vue
<template>
  <div>
    <h2>CategoryTreeSelect Test</h2>
    <CategoryTreeSelect v-model="categoryId" />
    <p>Selected: {{ categoryId }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CategoryTreeSelect } from '@/components/pointShop'

const categoryId = ref<string | null>(null)
</script>
```

---

## API Integration

All components integrate with existing API modules:

- **CategoryTreeSelect** → `@/api/pointCategory.ts` (getCategoryTree)
- **CourierSelect** → `@/api/courier.ts` (listActiveCouriers, listCouriers)
- **AddressForm** → Uses region data (can be extended to load from API)
- **RegionPricingForm** → Works with ShippingTemplate pricing config

---

## Future Enhancements

Potential improvements:

1. **SpecEditor.vue** - Extract specification editing from PointShop.vue
2. **SKUTable.vue** - Extract SKU table from PointShop.vue
3. **Region Cascader** - Replace mock region data with API/complete data file
4. **Component Tests** - Add Vitest unit tests for each component
5. **Storybook Stories** - Add .stories.vue files for visual testing
