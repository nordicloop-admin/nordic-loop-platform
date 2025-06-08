# 📋 Frontend Choice Values Reference - Nordic Loop Ads

This document contains **ALL exact values** that must be sent by the frontend for choice fields in the ad creation system. Use these EXACT strings to avoid validation errors.

## 🎯 Step 1: Material Type

### **`packaging`** (String - Required)
```javascript
// Valid options:
"baled"           // Baled
"loose"           // Loose  
"big_bag"         // Big-bag
"octabin"         // Octabin
"roles"           // Roles
"container"       // Container
"other"           // Other
```

### **`material_frequency`** (String - Required)
```javascript
// Valid options:
"one_time"        // One-time
"weekly"          // Weekly
"bi_weekly"       // Bi-weekly  
"monthly"         // Monthly
"quarterly"       // Quarterly
"yearly"          // Yearly
```

## 🎯 Step 3: Material Origin

### **`origin`** (String - Required)
```javascript
// Valid options:
"post_industrial" // Post-industrial
"post_consumer"   // Post-consumer
"mix"             // Mix
```

## 🎯 Step 4: Contamination

### **`contamination`** (String - Required)
```javascript
// Valid options:
"clean"                    // Clean
"slightly_contaminated"    // Slightly Contaminated  
"heavily_contaminated"     // Heavily Contaminated
```

### **`additives`** (String - Required)
```javascript
// Valid options:
"uv_stabilizer"     // UV Stabilizer
"antioxidant"       // Antioxidant
"flame_retardants"  // Flame retardants
"chlorides"         // Chlorides
"no_additives"      // No additives
```

### **`storage_conditions`** (String - Required)
```javascript
// Valid options:
"climate_controlled"   // Climate Controlled
"protected_outdoor"    // Protected Outdoor
"unprotected_outdoor"  // Unprotected Outdoor
```

## 🎯 Step 5: Processing Methods

### **`processing_methods`** (Array - At least one required)
```javascript
// Valid options (send as array):
[
  "blow_moulding",      // Blow moulding
  "injection_moulding", // Injection moulding
  "extrusion",          // Extrusion
  "calendering",        // Calendering
  "rotational_moulding", // Rotational moulding
  "sintering",          // Sintering
  "thermoforming"       // Thermoforming
]

// Example - send multiple methods:
{
  "processing_methods": ["extrusion", "injection_moulding", "blow_moulding"]
}

// Example - send single method:
{
  "processing_methods": ["extrusion"]
}
```

## 🎯 Step 6: Location & Logistics

### **`delivery_options`** (Array - At least one required)
```javascript
// Valid options (send as array):
[
  "pickup_only",           // Pickup Only
  "local_delivery",        // Local Delivery
  "national_shipping",     // National Shipping
  "international_shipping", // International Shipping
  "freight_forwarding"     // Freight Forwarding
]

// Example - send multiple options:
{
  "delivery_options": ["local_delivery", "national_shipping"]
}

// Example - send single option:
{
  "delivery_options": ["pickup_only"]
}
```

### **`pickup_available`** (Boolean - Required)
```javascript
// Valid options:
true    // Pickup is available
false   // Pickup not available
```

## 🎯 Step 7: Quantity & Pricing

### **`unit_of_measurement`** (String - Required)
```javascript
// Valid options:
"kg"    // Kilogram
"g"     // Gram
"lb"    // Pound
"tons"  // Tons
```

### **`currency`** (String - Required)
```javascript
// Valid options:
"EUR"   // Euro
"USD"   // US Dollar
"SEK"   // Swedish Krona
"GBP"   // British Pound
```

### **`auction_duration`** (Integer - Required)
```javascript
// Valid options:
1       // 1 day
3       // 3 days
7       // 7 days
14      // 14 days
30      // 30 days
```

## 🎯 Legacy/Additional Choices (Not used in 8-step process)

### **`selling_type`** (String - Optional/Legacy)
```javascript
// Valid options:
"partition"               // Selling in Partition
"whole"                   // Selling as Whole
"both whole and partion"  // selling as whole and partion
```

## 🔍 **Complete Step-by-Step Examples**

### **Step 1 Example:**
```javascript
{
  "category_id": 1,
  "subcategory_id": 1,
  "specific_material": "High-grade HDPE bottles",
  "packaging": "baled",           // ✅ EXACT VALUE
  "material_frequency": "weekly"  // ✅ EXACT VALUE
}
```

### **Step 3 Example:**
```javascript
{
  "origin": "post_industrial"     // ✅ EXACT VALUE
}
```

### **Step 4 Example:**
```javascript
{
  "contamination": "clean",              // ✅ EXACT VALUE
  "additives": "antioxidant",            // ✅ EXACT VALUE
  "storage_conditions": "climate_controlled"  // ✅ EXACT VALUE
}
```

### **Step 5 Example:**
```javascript
{
  "processing_methods": [               // ✅ ARRAY FORMAT
    "extrusion", 
    "injection_moulding", 
    "blow_moulding"
  ]
}
```

### **Step 6 Example:**
```javascript
{
  "location_data": {
    "country": "Sweden",
    "state_province": "Stockholm County",
    "city": "Stockholm",
    "address_line": "123 Industrial St",
    "postal_code": "11122"
  },
  "pickup_available": true,             // ✅ BOOLEAN
  "delivery_options": [                 // ✅ ARRAY FORMAT
    "local_delivery", 
    "national_shipping"
  ]
}
```

### **Step 7 Example:**
```javascript
{
  "available_quantity": 100.00,         // Decimal
  "unit_of_measurement": "tons",        // ✅ EXACT VALUE
  "minimum_order_quantity": 5.00,      // Decimal
  "starting_bid_price": 50.00,         // Decimal
  "currency": "EUR",                    // ✅ EXACT VALUE
  "auction_duration": 7,                // ✅ INTEGER VALUE
  "reserve_price": 75.00                // Decimal (optional)
}
```

## ⚠️ **Critical Validation Rules**

### **String Fields:**
- Must match EXACTLY (case-sensitive)
- No extra spaces, capitalization differences, or hyphens vs underscores

### **Array Fields:**
- Must be sent as arrays `[]`, even for single values
- Each array element must match exact string values

### **Boolean Fields:**
- Must be `true` or `false` (not strings `"true"` or `"false"`)

### **Integer Fields:**
- Must be integers, not strings (e.g., `7` not `"7"`)

### **Decimal Fields:**
- Can be integers or decimals (e.g., `100.00` or `100`)
- Must be positive numbers where specified

## 🛠️ **Frontend Implementation Helper**

### **JavaScript Constants:**
```javascript
// Define all choice constants
export const AD_CHOICES = {
  PACKAGING: {
    BALED: 'baled',
    LOOSE: 'loose',
    BIG_BAG: 'big_bag',
    OCTABIN: 'octabin',
    ROLES: 'roles',
    CONTAINER: 'container',
    OTHER: 'other'
  },
  
  MATERIAL_FREQUENCY: {
    ONE_TIME: 'one_time',
    WEEKLY: 'weekly',
    BI_WEEKLY: 'bi_weekly',
    MONTHLY: 'monthly',
    QUARTERLY: 'quarterly',
    YEARLY: 'yearly'
  },
  
  ORIGIN: {
    POST_INDUSTRIAL: 'post_industrial',
    POST_CONSUMER: 'post_consumer',
    MIX: 'mix'
  },
  
  CONTAMINATION: {
    CLEAN: 'clean',
    SLIGHTLY_CONTAMINATED: 'slightly_contaminated',
    HEAVILY_CONTAMINATED: 'heavily_contaminated'
  },
  
  ADDITIVES: {
    UV_STABILIZER: 'uv_stabilizer',
    ANTIOXIDANT: 'antioxidant',
    FLAME_RETARDANTS: 'flame_retardants',
    CHLORIDES: 'chlorides',
    NO_ADDITIVES: 'no_additives'
  },
  
  STORAGE_CONDITIONS: {
    CLIMATE_CONTROLLED: 'climate_controlled',
    PROTECTED_OUTDOOR: 'protected_outdoor',
    UNPROTECTED_OUTDOOR: 'unprotected_outdoor'
  },
  
  PROCESSING_METHODS: {
    BLOW_MOULDING: 'blow_moulding',
    INJECTION_MOULDING: 'injection_moulding',
    EXTRUSION: 'extrusion',
    CALENDERING: 'calendering',
    ROTATIONAL_MOULDING: 'rotational_moulding',
    SINTERING: 'sintering',
    THERMOFORMING: 'thermoforming'
  },
  
  DELIVERY_OPTIONS: {
    PICKUP_ONLY: 'pickup_only',
    LOCAL_DELIVERY: 'local_delivery',
    NATIONAL_SHIPPING: 'national_shipping',
    INTERNATIONAL_SHIPPING: 'international_shipping',
    FREIGHT_FORWARDING: 'freight_forwarding'
  },
  
  UNIT_OF_MEASUREMENT: {
    KG: 'kg',
    G: 'g',
    LB: 'lb',
    TONS: 'tons'
  },
  
  CURRENCY: {
    EUR: 'EUR',
    USD: 'USD',
    SEK: 'SEK',
    GBP: 'GBP'
  },
  
  AUCTION_DURATION: {
    ONE_DAY: 1,
    THREE_DAYS: 3,
    SEVEN_DAYS: 7,
    FOURTEEN_DAYS: 14,
    THIRTY_DAYS: 30
  }
};

// Usage example:
const step1Data = {
  category_id: 1,
  subcategory_id: 1,
  specific_material: "High-grade HDPE bottles",
  packaging: AD_CHOICES.PACKAGING.BALED,
  material_frequency: AD_CHOICES.MATERIAL_FREQUENCY.WEEKLY
};
```

### **Dropdown Options for UI:**
```javascript
// For creating dropdown/select components
export const DROPDOWN_OPTIONS = {
  packaging: [
    { value: 'baled', label: 'Baled' },
    { value: 'loose', label: 'Loose' },
    { value: 'big_bag', label: 'Big-bag' },
    { value: 'octabin', label: 'Octabin' },
    { value: 'roles', label: 'Roles' },
    { value: 'container', label: 'Container' },
    { value: 'other', label: 'Other' }
  ],
  
  materialFrequency: [
    { value: 'one_time', label: 'One-time' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'bi_weekly', label: 'Bi-weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'quarterly', label: 'Quarterly' },
    { value: 'yearly', label: 'Yearly' }
  ],
  
  origin: [
    { value: 'post_industrial', label: 'Post-industrial' },
    { value: 'post_consumer', label: 'Post-consumer' },
    { value: 'mix', label: 'Mix' }
  ],
  
  contamination: [
    { value: 'clean', label: 'Clean' },
    { value: 'slightly_contaminated', label: 'Slightly Contaminated' },
    { value: 'heavily_contaminated', label: 'Heavily Contaminated' }
  ],
  
  additives: [
    { value: 'uv_stabilizer', label: 'UV Stabilizer' },
    { value: 'antioxidant', label: 'Antioxidant' },
    { value: 'flame_retardants', label: 'Flame retardants' },
    { value: 'chlorides', label: 'Chlorides' },
    { value: 'no_additives', label: 'No additives' }
  ],
  
  storageConditions: [
    { value: 'climate_controlled', label: 'Climate Controlled' },
    { value: 'protected_outdoor', label: 'Protected Outdoor' },
    { value: 'unprotected_outdoor', label: 'Unprotected Outdoor' }
  ],
  
  processingMethods: [
    { value: 'blow_moulding', label: 'Blow moulding' },
    { value: 'injection_moulding', label: 'Injection moulding' },
    { value: 'extrusion', label: 'Extrusion' },
    { value: 'calendering', label: 'Calendering' },
    { value: 'rotational_moulding', label: 'Rotational moulding' },
    { value: 'sintering', label: 'Sintering' },
    { value: 'thermoforming', label: 'Thermoforming' }
  ],
  
  deliveryOptions: [
    { value: 'pickup_only', label: 'Pickup Only' },
    { value: 'local_delivery', label: 'Local Delivery' },
    { value: 'national_shipping', label: 'National Shipping' },
    { value: 'international_shipping', label: 'International Shipping' },
    { value: 'freight_forwarding', label: 'Freight Forwarding' }
  ],
  
  unitOfMeasurement: [
    { value: 'kg', label: 'Kilogram' },
    { value: 'g', label: 'Gram' },
    { value: 'lb', label: 'Pound' },
    { value: 'tons', label: 'Tons' }
  ],
  
  currency: [
    { value: 'EUR', label: 'Euro' },
    { value: 'USD', label: 'US Dollar' },
    { value: 'SEK', label: 'Swedish Krona' },
    { value: 'GBP', label: 'British Pound' }
  ],
  
  auctionDuration: [
    { value: 1, label: '1 day' },
    { value: 3, label: '3 days' },
    { value: 7, label: '7 days' },
    { value: 14, label: '14 days' },
    { value: 30, label: '30 days' }
  ]
};
```

## 🎯 **Common Mistakes to Avoid**

### ❌ **Wrong:**
```javascript
{
  "packaging": "Baled",           // Capital B
  "material_frequency": "one-time", // Hyphen instead of underscore
  "processing_methods": "extrusion", // String instead of array
  "pickup_available": "true",     // String instead of boolean
  "auction_duration": "7"         // String instead of integer
}
```

### ✅ **Correct:**
```javascript
{
  "packaging": "baled",           // Lowercase
  "material_frequency": "one_time", // Underscore
  "processing_methods": ["extrusion"], // Array
  "pickup_available": true,       // Boolean
  "auction_duration": 7           // Integer
}
```

---

**Always refer to this document when implementing choice fields in the frontend to ensure 100% validation success!** 

# Frontend Choice Values Reference

This document provides a comprehensive reference for all choice values and form options available in the Nordic Loop Platform API.

## Getting Choice Values

### API Endpoints

```bash
# Get all ad form choices (units, durations, etc.)
GET /api/category/ad-form-choices/

# Get specification choices (colors, grades, forms)
GET /api/category/specification-choices/
```

## Units of Measurement

The platform now supports a comprehensive list of units for different material types:

### Available Units
```javascript
const units = [
  { value: 'kg', label: 'Kilogram' },
  { value: 'tons', label: 'Tons' },
  { value: 'tonnes', label: 'Tonnes' },
  { value: 'lbs', label: 'Pounds' },
  { value: 'pounds', label: 'Pounds' },
  { value: 'pieces', label: 'Pieces' },
  { value: 'units', label: 'Units' },
  { value: 'bales', label: 'Bales' },
  { value: 'containers', label: 'Containers' },
  { value: 'm³', label: 'Cubic Meters' },
  { value: 'cubic_meters', label: 'Cubic Meters' },
  { value: 'liters', label: 'Liters' },
  { value: 'gallons', label: 'Gallons' }
];
```

### Usage Examples by Material Type

- **Plastics**: `kg`, `tons`, `tonnes`, `pieces`, `liters` (for granules)
- **Metals**: `kg`, `tons`, `tonnes`, `pieces` (for components)
- **Paper**: `kg`, `tons`, `bales`
- **Glass**: `kg`, `tons`, `pieces`, `units` (for bottles)
- **Textiles**: `kg`, `tons`, `bales`
- **Chemicals**: `liters`, `gallons`, `containers`, `pieces` (for containers)
- **Building Materials**: `tons`, `tonnes`, `m³`, `cubic_meters`, `pieces`

## Auction Duration Options

### Available Durations
```javascript
const auctionDurations = [
  { value: 1, label: '1 day' },
  { value: 3, label: '3 days' },
  { value: 7, label: '7 days' },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
  { value: 0, label: 'Custom' }  // NEW: Custom duration option
];
```

### Custom Duration Implementation

When `auction_duration` is set to `0` (Custom), you must provide a `custom_auction_duration` value:

```javascript
// Example form handling
const [auctionDuration, setAuctionDuration] = useState(7);
const [customDuration, setCustomDuration] = useState('');

const handleDurationChange = (value) => {
  setAuctionDuration(value);
  if (value !== 0) {
    setCustomDuration(''); // Clear custom duration for predefined options
  }
};

// API payload
const adData = {
  auction_duration: auctionDuration,
  custom_auction_duration: auctionDuration === 0 ? parseInt(customDuration) : null,
  // ... other fields
};
```

### Frontend Form Example
```jsx
const AuctionDurationField = () => {
  const [duration, setDuration] = useState(7);
  const [customDays, setCustomDays] = useState('');

  return (
    <div>
      <select 
        value={duration} 
        onChange={(e) => setDuration(parseInt(e.target.value))}
      >
        <option value={1}>1 day</option>
        <option value={3}>3 days</option>
        <option value={7}>7 days</option>
        <option value={14}>14 days</option>
        <option value={30}>30 days</option>
        <option value={0}>Custom</option>
      </select>
      
      {duration === 0 && (
        <input
          type="number"
          min="1"
          placeholder="Enter days"
          value={customDays}
          onChange={(e) => setCustomDays(e.target.value)}
          required
        />
      )}
    </div>
  );
};
```

## Material Specifications

### Material Colors
```javascript
const materialColors = [
  { value: 'natural_clear', label: 'Natural/Clear' },
  { value: 'white', label: 'White' },
  { value: 'black', label: 'Black' },
  { value: 'red', label: 'Red' },
  { value: 'blue', label: 'Blue' },
  { value: 'green', label: 'Green' },
  { value: 'yellow', label: 'Yellow' },
  { value: 'orange', label: 'Orange' },
  { value: 'purple', label: 'Purple' },
  { value: 'brown', label: 'Brown' },
  { value: 'gray', label: 'Gray' },
  { value: 'mixed_colors', label: 'Mixed Colors' },
  { value: 'custom_color', label: 'Custom Color' }
];
```

### Material Grades
```javascript
const materialGrades = [
  { value: 'virgin_grade', label: 'Virgin Grade' },
  { value: 'industrial_grade', label: 'Industrial Grade' },
  { value: 'food_grade', label: 'Food Grade' },
  { value: 'medical_grade', label: 'Medical Grade' },
  { value: 'automotive_grade', label: 'Automotive Grade' },
  { value: 'electrical_grade', label: 'Electrical Grade' },
  { value: 'recycled_grade', label: 'Recycled Grade' }
];
```

### Material Forms
```javascript
const materialForms = [
  { value: 'pellets_granules', label: 'Pellets/Granules' },
  { value: 'flakes', label: 'Flakes' },
  { value: 'regrind', label: 'Regrind' },
  { value: 'sheets', label: 'Sheets' },
  { value: 'film', label: 'Film' },
  { value: 'parts_components', label: 'Parts/Components' },
  { value: 'powder', label: 'Powder' },
  { value: 'fiber', label: 'Fiber' }
];
```

## Step 7 API Usage (Quantity & Pricing)

### Request Example
```javascript
const step7Data = {
  available_quantity: "25000.00",
  unit_of_measurement: "units",
  minimum_order_quantity: "1000.00",
  starting_bid_price: "0.45",
  currency: "EUR",
  auction_duration: 0,  // Custom duration
  custom_auction_duration: 12,  // 12 days custom
  reserve_price: "0.65"
};

// API call
const response = await fetch('/api/ads/{id}/step7/', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify(step7Data)
});
```

### Validation Rules

1. **Custom Duration**: Required when `auction_duration = 0`
2. **Units**: Must be one of the supported unit types
3. **Minimum Order**: Cannot exceed available quantity
4. **Reserve Price**: Must be greater than or equal to starting price
5. **Custom Duration**: Must be at least 1 day

### Error Handling
```javascript
// Example error responses
{
  "error": "Custom auction duration is required when auction duration is set to 'Custom'."
}

{
  "error": "Custom auction duration should only be provided when auction duration is set to 'Custom'."
}

{
  "error": "Custom auction duration must be at least 1 day."
}
```

## Complete Form Choices API Response

```javascript
{
  "message": "Ad form choices retrieved successfully",
  "data": {
    "units": [...],
    "auction_durations": [...],
    "currencies": [...],
    "packaging": [...],
    "material_frequencies": [...],
    "material_origins": [...],
    "contamination_levels": [...],
    "additives": [...],
    "storage_conditions": [...],
    "processing_methods": [...],
    "delivery_options": [...]
  }
}
```

## Real-World Examples

### Example 1: Glass Bottles by Units
```javascript
const glassBottleAd = {
  title: "Premium Wine Bottles",
  available_quantity: "25000.00",
  unit_of_measurement: "units",
  starting_bid_price: "0.45",  // €0.45 per bottle
  minimum_order_quantity: "1000.00",
  auction_duration: 14
};
```

### Example 2: Chemical Containers by Pieces
```javascript
const containerAd = {
  title: "Industrial Chemical Containers",
  available_quantity: "1500.00",
  unit_of_measurement: "pieces",
  starting_bid_price: "12.50",  // €12.50 per container
  minimum_order_quantity: "100.00",
  auction_duration: 0,
  custom_auction_duration: 12
};
```

### Example 3: Plastic Granules by Volume
```javascript
const granuleAd = {
  title: "Recycled Plastic Granules",
  available_quantity: "50000.00",
  unit_of_measurement: "liters",
  starting_bid_price: "0.85",  // €0.85 per liter
  minimum_order_quantity: "5000.00",
  auction_duration: 7
};
```

## Frontend Implementation Tips

1. **Dynamic Unit Selection**: Show appropriate units based on material category
2. **Conditional Custom Duration**: Only show custom duration input when "Custom" is selected
3. **Real-time Validation**: Validate custom duration and unit combinations client-side
4. **Price Calculation**: Display total value calculations in real-time
5. **Unit Display**: Show units consistently throughout the interface (listings, details, bids)

## API Testing

```bash
# Test new units endpoint
curl -X GET "http://localhost:8000/api/category/ad-form-choices/"

# Test ad creation with custom duration
curl -X POST "http://localhost:8000/api/ads/{id}/step7/" \
  -H "Content-Type: application/json" \
  -d '{
    "auction_duration": 0,
    "custom_auction_duration": 15,
    "unit_of_measurement": "pieces",
    "available_quantity": "1000.00"
  }'
```

This reference should provide everything needed to implement the new unit types and custom auction duration functionality in the frontend. 