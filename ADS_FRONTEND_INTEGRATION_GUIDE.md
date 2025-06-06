# 📋 Nordic Loop 8-Step Ad Creation - Frontend Integration Guide

This guide provides comprehensive instructions for integrating with the enhanced 8-step ad creation system API.

## 🔐 Authentication Requirements

All ad creation endpoints require JWT authentication. Include the access token in the Authorization header:

```javascript
Authorization: Bearer <access_token>
```

**Get Authentication Token:**
```javascript
POST /api/users/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

// Response:
{
  "message": "Login successful.",
  "username": "username",
  "email": "user@example.com",
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

## 🎯 8-Step Ad Creation Workflow

### Overview of Steps
1. **Material Type** - Basic material categorization and packaging
2. **Specifications** - Detailed material specifications  
3. **Material Origin** - Source of the material
4. **Contamination** - Contamination level and storage conditions
5. **Processing Methods** - Applicable processing methods
6. **Location & Logistics** - Material location and delivery options
7. **Quantity & Pricing** - Auction pricing and quantities
8. **Title, Description & Image** - Final listing details

### Important HTTP Methods
- **POST** - Only for Step 1 (creating new ad)
- **PUT** - For Steps 2-8 (updating existing ad)
- **GET** - Retrieve step data

## 📝 Step-by-Step Implementation

### Step 1: Material Type (Create New Ad)

**Endpoint:** `POST /api/ads/step/1/`

**Required Fields:**
```javascript
{
  "category_id": 1,                    // Integer: Category ID (required)
  "subcategory_id": 1,                 // Integer: Subcategory ID (required)
  "specific_material": "Test HDPE material",  // String: Material description (required)
  "packaging": "octabin",              // String: Packaging type (required)
  "material_frequency": "monthly"      // String: Supply frequency (required)
}
```

**Success Response (201):**
```javascript
{
  "message": "Material ad created successfully with Step 1 data. Continue with Step 2.",
  "step": 1,
  "data": {
    "id": 14,                          // ⭐ SAVE THIS AD_ID for subsequent steps
    "category_name": "Plastics",
    "subcategory_name": "PP",
    "specific_material": "Test HDPE material",
    "packaging": "octabin",
    "material_frequency": "monthly",
    "current_step": 2
  },
  "step_completion_status": {
    "1": true,
    "2": false,
    "3": false,
    // ... all steps
  },
  "next_incomplete_step": 2,
  "is_complete": false
}
```

**Packaging Options:**
- `"baled"` - Baled
- `"loose"` - Loose  
- `"big_bag"` - Big-bag
- `"octabin"` - Octabin
- `"roles"` - Roles
- `"container"` - Container
- `"other"` - Other

**Material Frequency Options:**
- `"one_time"` - One-time
- `"weekly"` - Weekly
- `"bi_weekly"` - Bi-weekly
- `"monthly"` - Monthly
- `"quarterly"` - Quarterly
- `"yearly"` - Yearly

### Step 2: Specifications

**Endpoint:** `PUT /api/ads/{ad_id}/step/2/`

**Required Fields:**
```javascript
{
  "specification_id": null,           // Integer or null: Pre-defined specification ID
  "additional_specifications": "Melt Flow Index: 2.5, Density: 0.95 g/cm³, Food grade certification, FDA approved"  // String: Custom specifications
}
```

**Success Response (200):**
```javascript
{
  "message": "Step 2 updated successfully",
  "step": 2,
  "data": {
    "id": 14,
    "specification": null,
    "additional_specifications": "Melt Flow Index: 2.5, Density: 0.95 g/cm³, Food grade certification, FDA approved",
    "current_step": 3
  },
  "step_completion_status": {
    "1": true,
    "2": true,
    "3": false,
    // ...
  },
  "next_incomplete_step": 3,
  "is_complete": false
}
```

**Note:** Either `specification_id` OR `additional_specifications` is required for step completion.

### Step 3: Material Origin

**Endpoint:** `PUT /api/ads/{ad_id}/step/3/`

**Required Fields:**
```javascript
{
  "origin": "post_industrial"         // String: Material origin (required)
}
```

**Origin Options:**
- `"post_industrial"` - Post-industrial
- `"post_consumer"` - Post-consumer  
- `"mix"` - Mix

### Step 4: Contamination

**Endpoint:** `PUT /api/ads/{ad_id}/step/4/`

**Required Fields (ALL REQUIRED):**
```javascript
{
  "contamination": "clean",           // String: Contamination level (required)
  "additives": "antioxidant",         // String: Additives present (required)
  "storage_conditions": "climate_controlled"  // String: Storage conditions (required)
}
```

**Contamination Options:**
- `"clean"` - Clean
- `"slightly_contaminated"` - Slightly Contaminated
- `"heavily_contaminated"` - Heavily Contaminated

**Additives Options:**
- `"uv_stabilizer"` - UV Stabilizer
- `"antioxidant"` - Antioxidant
- `"flame_retardants"` - Flame retardants
- `"chlorides"` - Chlorides
- `"no_additives"` - No additives

**Storage Conditions Options:**
- `"climate_controlled"` - Climate Controlled
- `"protected_outdoor"` - Protected Outdoor
- `"unprotected_outdoor"` - Unprotected Outdoor

### Step 5: Processing Methods

**Endpoint:** `PUT /api/ads/{ad_id}/step/5/`

**Required Fields:**
```javascript
{
  "processing_methods": [             // Array: Processing methods (at least one required)
    "extrusion", 
    "injection_moulding", 
    "blow_moulding"
  ]
}
```

**Processing Methods Options:**
- `"blow_moulding"` - Blow moulding
- `"injection_moulding"` - Injection moulding
- `"extrusion"` - Extrusion
- `"calendering"` - Calendering
- `"rotational_moulding"` - Rotational moulding
- `"sintering"` - Sintering
- `"thermoforming"` - Thermoforming

### Step 6: Location & Logistics

**Endpoint:** `PUT /api/ads/{ad_id}/step/6/`

**Required Fields:**
```javascript
{
  "location_data": {                  // Object: Location information (required)
    "country": "Sweden",
    "state_province": "Stockholm County",  // Optional
    "city": "Stockholm",
    "address_line": "123 Industrial St",  // Optional
    "postal_code": "11122"
  },
  "pickup_available": true,           // Boolean: Pickup availability
  "delivery_options": [               // Array: Delivery options (at least one required)
    "local_delivery", 
    "national_shipping"
  ]
}
```

**Delivery Options:**
- `"pickup_only"` - Pickup Only
- `"local_delivery"` - Local Delivery
- `"national_shipping"` - National Shipping
- `"international_shipping"` - International Shipping
- `"freight_forwarding"` - Freight Forwarding

### Step 7: Quantity & Pricing

**Endpoint:** `PUT /api/ads/{ad_id}/step/7/`

**Required Fields:**
```javascript
{
  "available_quantity": 100.00,       // Decimal: Total quantity (required, > 0)
  "unit_of_measurement": "tons",      // String: Unit type (required)
  "minimum_order_quantity": 5.00,    // Decimal: Min order quantity (required, >= 0)
  "starting_bid_price": 50.00,       // Decimal: Starting bid price (required, > 0)
  "currency": "EUR",                  // String: Currency (required)
  "auction_duration": 7,              // Integer: Auction duration in days (required)
  "reserve_price": 75.00              // Decimal: Reserve price (optional, must be >= starting_bid_price)
}
```

**Unit of Measurement Options:**
- `"kg"` - Kilogram
- `"g"` - Gram
- `"lb"` - Pound
- `"tons"` - Tons

**Currency Options:**
- `"EUR"` - Euro
- `"USD"` - US Dollar
- `"SEK"` - Swedish Krona
- `"GBP"` - British Pound

**Auction Duration Options:**
- `1` - 1 day
- `3` - 3 days
- `7` - 7 days
- `14` - 14 days
- `30` - 30 days

**Validation Rules:**
- `minimum_order_quantity` cannot exceed `available_quantity`
- `reserve_price` cannot be lower than `starting_bid_price`

### Step 8: Title, Description & Image (Final Step)

**Endpoint:** `PUT /api/ads/{ad_id}/step/8/`

**Required Fields:**
```javascript
{
  "title": "Premium HDPE Material - High Quality",        // String: Title (min 10 chars, required)
  "description": "High-quality HDPE material perfect for manufacturing applications. Clean, sorted, and ready for processing.",  // String: Description (min 50 chars, required)
  "keywords": "HDPE, plastic, recycling, manufacturing"   // String: Keywords (optional)
}
```

**Success Response (Ad Complete):**
```javascript
{
  "message": "Material ad completed successfully! Your material is now listed for auction.",
  "step": 8,
  "data": {
    "id": 14,
    "title": "Premium HDPE Material - High Quality",
    "description": "High-quality HDPE material perfect...",
    "keywords": "HDPE, plastic, recycling, manufacturing",
    "current_step": 8,
    "is_complete": true
  },
  "step_completion_status": {
    "1": true,
    "2": true,
    "3": true,
    "4": true,
    "5": true,
    "6": true,
    "7": true,
    "8": true
  },
  "next_incomplete_step": null,
  "is_complete": true
}
```

## 📖 Additional API Endpoints

### Get Step Data
**Endpoint:** `GET /api/ads/{ad_id}/step/{step}/`

**Example:** `GET /api/ads/14/step/3/`

**Response:**
```javascript
{
  "step": 3,
  "data": {
    "id": 14,
    "origin": "post_industrial",
    "current_step": 5
  },
  "step_completion_status": {
    "1": true,
    "2": true,
    "3": true,
    // ...
  },
  "next_incomplete_step": 4
}
```

### Validate Step Data (Optional)
**Endpoint:** `POST /api/ads/validate/step/{step}/`

**Example:** `POST /api/ads/validate/step/4/`

**Request Body:**
```javascript
{
  "contamination": "clean",
  "additives": "antioxidant",
  "storage_conditions": "climate_controlled"
}
```

**Response:**
```javascript
{
  "valid": true,
  "message": "Step 4 data is valid"
}
```

### Get Complete Ad Details
**Endpoint:** `GET /api/ads/{ad_id}/`

### List User's Ads
**Endpoint:** `GET /api/ads/user/`

**Query Parameters:**
- `complete=true` - Only show completed ads
- `complete=false` - Show all ads (including in-progress)

### Delete Ad
**Endpoint:** `DELETE /api/ads/{ad_id}/`

## ⚠️ Error Handling

**Common Error Codes:**
- `400` - Bad Request (validation errors, wrong method)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (permission denied)
- `404` - Not Found (ad doesn't exist)
- `405` - Method Not Allowed (wrong HTTP method)
- `500` - Server Error

**Error Response Format:**
```javascript
{
  "error": "Validation failed",
  "details": {
    "contamination": ["This field is required."],
    "additives": ["This field is required."]
  }
}
```

**Frontend Error Handling Strategy:**
```javascript
try {
  const response = await fetch(`/api/ads/${adId}/step/4/`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(stepData)
  });
  
  const result = await response.json();
  
  if (response.ok) {
    // Success - move to next step
    updateProgress(result.step_completion_status);
    if (result.is_complete) {
      showCompletionMessage();
    } else {
      goToStep(result.next_incomplete_step);
    }
  } else {
    // Error - show validation messages
    showErrorMessages(result.details || result.error);
  }
} catch (error) {
  // Network/server error
  showErrorMessage('Connection error. Please try again.');
}
```

## 🚀 Frontend Implementation Example

### Complete Workflow Implementation

```javascript
class AdCreationService {
  constructor(apiBaseUrl, authToken) {
    this.apiBaseUrl = apiBaseUrl;
    this.authToken = authToken;
    this.currentAdId = null;
  }

  async createAdStep1(data) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/ads/step/1/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();
      
      if (response.ok) {
        this.currentAdId = result.data.id; // Save ad ID for subsequent steps
        return { success: true, data: result };
      } else {
        return { success: false, error: result.error, details: result.details };
      }
    } catch (error) {
      return { success: false, error: 'Network error', details: error.message };
    }
  }

  async updateAdStep(step, data) {
    if (!this.currentAdId) {
      throw new Error('No active ad. Please complete Step 1 first.');
    }

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/ads/${this.currentAdId}/step/${step}/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();
      
      if (response.ok) {
        return { success: true, data: result };
      } else {
        return { success: false, error: result.error, details: result.details };
      }
    } catch (error) {
      return { success: false, error: 'Network error', details: error.message };
    }
  }

  async getStepData(step) {
    if (!this.currentAdId) {
      throw new Error('No active ad selected.');
    }

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/ads/${this.currentAdId}/step/${step}/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.authToken}`
        }
      });

      const result = await response.json();
      return response.ok ? { success: true, data: result } : { success: false, error: result.error };
    } catch (error) {
      return { success: false, error: 'Network error', details: error.message };
    }
  }
}

// Usage Example
const adService = new AdCreationService('http://localhost:8000', userToken);

// Step 1: Create new ad
const step1Result = await adService.createAdStep1({
  category_id: 1,
  subcategory_id: 1,
  specific_material: "High-grade HDPE bottles",
  packaging: "baled",
  material_frequency: "weekly"
});

if (step1Result.success) {
  console.log('Ad created with ID:', adService.currentAdId);
  
  // Step 2: Add specifications
  const step2Result = await adService.updateAdStep(2, {
    specification_id: null,
    additional_specifications: "Clean, sorted bottles. Food grade quality."
  });
  
  // Continue with remaining steps...
}
```

### UI Component Suggestions

### 1. Step Progress Indicator
```javascript
// Show progress and allow navigation to completed steps
const StepProgress = ({ completionStatus, currentStep, onStepClick }) => {
  return (
    <div className="step-progress">
      {[1,2,3,4,5,6,7,8].map(step => (
        <div 
          key={step}
          className={`step ${completionStatus[step] ? 'completed' : ''} ${currentStep === step ? 'active' : ''}`}
          onClick={() => completionStatus[step] && onStepClick(step)}
        >
          Step {step}
        </div>
      ))}
    </div>
  );
};
```

### 2. Dynamic Form Validation
```javascript
// Real-time validation for each step
const validateStep4 = (data) => {
  const errors = {};
  
  if (!data.contamination) {
    errors.contamination = 'Contamination level is required';
  }
  
  if (!data.additives) {
    errors.additives = 'Additives information is required';
  }
  
  if (!data.storage_conditions) {
    errors.storage_conditions = 'Storage conditions are required';
  }
  
  return { isValid: Object.keys(errors).length === 0, errors };
};
```

### 3. Auto-save Functionality
```javascript
// Auto-save step data as user types
const useAutoSave = (adService, step, data, delay = 2000) => {
  useEffect(() => {
    if (!data || Object.keys(data).length === 0) return;
    
    const timeoutId = setTimeout(async () => {
      const result = await adService.updateAdStep(step, data);
      if (result.success) {
        showNotification('Changes saved automatically');
      }
    }, delay);
    
    return () => clearTimeout(timeoutId);
  }, [data, step, delay]);
};
```

## 📱 Mobile Optimization Tips

**Key mobile considerations:**
- **Step-by-step navigation** with clear progress indicators
- **Touch-friendly** form inputs and dropdowns
- **Simplified forms** with smart defaults
- **Auto-save** functionality for interrupted sessions
- **Offline data caching** for poor connectivity
- **Image upload** with compression
- **Swipe navigation** between steps

## 🧪 Testing Guidelines

**Test with sample data:**

1. **Categories:** Use existing category/subcategory IDs from your database
2. **Complete Flow:** Test the entire 8-step process
3. **Validation:** Test required field validation for each step
4. **Error Handling:** Test with invalid data
5. **Step Navigation:** Test going back to previous steps
6. **Auto-save:** Test saving incomplete steps

## 📋 Complete API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ads/step/1/` | Create new ad with Step 1 data |
| `PUT` | `/api/ads/{ad_id}/step/{2-8}/` | Update Steps 2-8 |
| `GET` | `/api/ads/{ad_id}/step/{step}/` | Get step data |
| `POST` | `/api/ads/validate/step/{step}/` | Validate step data |
| `GET` | `/api/ads/{ad_id}/` | Get complete ad details |
| `DELETE` | `/api/ads/{ad_id}/` | Delete ad |
| `GET` | `/api/ads/user/` | List user's ads |
| `GET` | `/api/ads/` | List all complete ads |

## 🔄 Step Progression Logic

```
Step 1 (POST) → Step 2 (PUT) → Step 3 (PUT) → Step 4 (PUT) → Step 5 (PUT) → Step 6 (PUT) → Step 7 (PUT) → Step 8 (PUT) → COMPLETE ✅
```

- Each completed step automatically advances `current_step`
- Users can go back to edit previous steps (use `PUT` method)
- Step 8 completion sets `is_complete = true`
- Only complete ads appear in public listings

## 💡 Best Practices

1. **Always use POST for Step 1** (creates new ad)
2. **Always use PUT for Steps 2-8** (updates existing ad)
3. **Save the ad_id** from Step 1 response for all subsequent steps
4. **Handle step validation errors** gracefully with user-friendly messages
5. **Implement auto-save** for better user experience
6. **Show progress indicators** so users know where they are
7. **Allow navigation** to previous completed steps
8. **Validate data client-side** before sending to API
9. **Handle network errors** with retry functionality
10. **Cache form data locally** to prevent data loss

---

This comprehensive ad creation system provides a complete material listing experience with step-by-step validation, progress tracking, and robust error handling. The API is designed to guide users through the complete process while maintaining data integrity and user experience.

**Contact Backend Developer:** If you need any clarification or encounter issues, please reach out with specific error messages and request/response examples. 