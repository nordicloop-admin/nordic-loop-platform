# Ad Update Functionality Guide

## 🔄 Complete Ad Update System

The Nordic Loop platform now includes comprehensive ad update functionality that allows users to modify their material auction listings after creation. This guide covers all update capabilities and API endpoints.

## 🎯 Update Methods Available

### 1. **Step-by-Step Updates** (Existing)
- **Purpose**: Update individual steps of the 8-step ad creation process
- **Endpoints**: `PUT /api/ads/{ad_id}/step/{step}/`
- **Use Case**: When users want to modify specific sections of their ad

### 2. **Complete Ad Updates** (New)
- **Purpose**: Update the entire ad with all provided fields
- **Endpoint**: `PUT /api/ads/{ad_id}/`
- **Use Case**: When users want to overwrite/replace entire ad content

### 3. **Partial Ad Updates** (New)
- **Purpose**: Update only specific fields while keeping others unchanged
- **Endpoint**: `PATCH /api/ads/{ad_id}/`
- **Use Case**: When users want to modify just a few fields (most common)

## 📋 API Endpoints Overview

| Method | Endpoint | Purpose | Authentication |
|--------|----------|---------|----------------|
| `PUT` | `/api/ads/{ad_id}/step/{step}/` | Update specific step | Required |
| `PUT` | `/api/ads/{ad_id}/` | Complete ad update | Required |
| `PATCH` | `/api/ads/{ad_id}/` | Partial ad update | Required |
| `GET` | `/api/ads/{ad_id}/` | View ad details | Required |
| `DELETE` | `/api/ads/{ad_id}/` | Delete ad | Required |

## 🔧 Complete Ad Update (PUT)

### **Endpoint:** `PUT /api/ads/{ad_id}/`

**Purpose**: Replace/update the entire ad with provided data. All fields should be provided.

**Request Example:**
```json
{
  "category": 1,
  "subcategory": 1,
  "specific_material": "High-quality HDPE pellets",
  "packaging": "octabin",
  "material_frequency": "monthly",
  "additional_specifications": "Food grade certified, FDA approved",
  "origin": "post_industrial",
  "contamination": "clean",
  "additives": "uv_stabilizer",
  "storage_conditions": "climate_controlled",
  "processing_methods": ["extrusion", "injection_moulding"],
  "location_data": {
    "country": "Sweden",
    "state_province": "Stockholm County",
    "city": "Stockholm",
    "address_line": "Industrial Street 123",
    "postal_code": "11122"
  },
  "pickup_available": true,
  "delivery_options": ["local_delivery", "national_shipping"],
  "available_quantity": 100.0,
  "unit_of_measurement": "tons",
  "minimum_order_quantity": 5.0,
  "starting_bid_price": 50.0,
  "currency": "EUR",
  "auction_duration": 7,
  "reserve_price": 75.0,
  "title": "Premium HDPE Pellets - Food Grade",
  "description": "High-quality HDPE pellets suitable for food packaging applications. Clean, post-industrial material with excellent properties.",
  "keywords": "HDPE, pellets, food grade, industrial"
}
```

**Response:**
```json
{
  "message": "Ad updated successfully",
  "data": {
    "id": 26,
    "posted_by": "John Doe",
    "company_name": "Test Nordic Company AB",
    // ... all enhanced ad details
    "title": "Premium HDPE Pellets - Food Grade",
    "starting_bid_price": "50.00",
    "currency": "EUR",
    "current_step": 8,
    "is_complete": true,
    "updated_at": "2025-06-06T16:00:00Z"
  }
}
```

## 🎨 Partial Ad Update (PATCH)

### **Endpoint:** `PATCH /api/ads/{ad_id}/`

**Purpose**: Update only specific fields while keeping other fields unchanged. Most flexible and commonly used.

**Request Examples:**

#### Update Title & Description Only:
```json
{
  "title": "Updated Material Title",
  "description": "This is an updated description with more details about the material specifications and quality."
}
```

#### Update Pricing Information:
```json
{
  "starting_bid_price": 75.50,
  "reserve_price": 100.0,
  "currency": "USD"
}
```

#### Update Location:
```json
{
  "location_data": {
    "country": "Sweden", 
    "city": "Gothenburg",
    "state_province": "Västra Götaland",
    "postal_code": "41234"
  }
}
```

#### Update Processing Methods:
```json
{
  "processing_methods": ["extrusion", "blow_moulding", "thermoforming"]
}
```

#### Update Delivery Options:
```json
{
  "delivery_options": ["pickup_only", "local_delivery"],
  "pickup_available": true
}
```

**Response:**
```json
{
  "message": "Ad partially updated successfully",
  "data": {
    // ... complete updated ad data with enhanced details
  }
}
```

## 🔒 Security & Validation

### **Ownership Validation:**
- ✅ Users can only update their own ads
- ✅ Authentication required for all update operations
- ✅ Proper error responses for unauthorized access

### **Data Validation:**
- ✅ All field validations from original ad creation apply
- ✅ Cross-field validation (e.g., reserve price >= starting price)
- ✅ Quantity validation (min order <= available quantity)
- ✅ Choice field validation (valid enum values)
- ✅ Required field validation with clear error messages

### **Business Logic:**
- ✅ Automatic step completion calculation
- ✅ Ad completion status updates
- ✅ Location creation/update handling
- ✅ File upload support (images)

## 🎛️ Update Capabilities by Field

| Field Category | Update Method | Notes |
|----------------|---------------|-------|
| **Basic Info** | ✅ Full Support | Title, description, keywords |
| **Material Type** | ✅ Full Support | Category, subcategory, packaging, frequency |
| **Specifications** | ✅ Full Support | Specification ID, custom specifications |
| **Origin & Contamination** | ✅ Full Support | All contamination and storage fields |
| **Processing** | ✅ Full Support | Processing methods array |
| **Location** | ✅ Full Support | Complete address with coordinates |
| **Logistics** | ✅ Full Support | Delivery options, pickup availability |
| **Pricing** | ✅ Full Support | All pricing and quantity fields |
| **Images** | ✅ Full Support | Material image upload/update |
| **System Fields** | 🔒 Protected | User, creation date, auto-calculated fields |

## 🧪 Frontend Implementation Examples

### JavaScript Service Class

```javascript
class AdUpdateService {
  constructor(apiBaseUrl, authToken) {
    this.apiBaseUrl = apiBaseUrl;
    this.authToken = authToken;
  }

  async partialUpdateAd(adId, updateData) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/ads/${adId}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      const result = await response.json();
      
      if (response.ok) {
        return { success: true, data: result.data, message: result.message };
      } else {
        return { success: false, error: result.error, details: result.details };
      }
    } catch (error) {
      return { success: false, error: 'Network error', details: error.message };
    }
  }

  async completeUpdateAd(adId, adData) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/ads/${adId}/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(adData)
      });

      const result = await response.json();
      
      if (response.ok) {
        return { success: true, data: result.data, message: result.message };
      } else {
        return { success: false, error: result.error, details: result.details };
      }
    } catch (error) {
      return { success: false, error: 'Network error', details: error.message };
    }
  }

  async updateWithImage(adId, updateData, imageFile) {
    try {
      const formData = new FormData();
      
      // Add text fields
      Object.keys(updateData).forEach(key => {
        if (Array.isArray(updateData[key])) {
          formData.append(key, JSON.stringify(updateData[key]));
        } else {
          formData.append(key, updateData[key]);
        }
      });
      
      // Add image file
      if (imageFile) {
        formData.append('material_image', imageFile);
      }

      const response = await fetch(`${this.apiBaseUrl}/api/ads/${adId}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${this.authToken}`
          // Don't set Content-Type for FormData
        },
        body: formData
      });

      const result = await response.json();
      return response.ok ? 
        { success: true, data: result.data } : 
        { success: false, error: result.error };
    } catch (error) {
      return { success: false, error: 'Upload failed', details: error.message };
    }
  }
}

// Usage Examples
const updateService = new AdUpdateService('http://localhost:8000', userToken);

// Update just the title
await updateService.partialUpdateAd(26, {
  title: "New Improved Title"
});

// Update pricing
await updateService.partialUpdateAd(26, {
  starting_bid_price: 99.99,
  currency: "USD",
  reserve_price: 150.0
});

// Update location
await updateService.partialUpdateAd(26, {
  location_data: {
    country: "Sweden",
    city: "Stockholm",
    postal_code: "11122"
  }
});

// Complete update
await updateService.completeUpdateAd(26, {
  // ... all required fields
});
```

### React Hook Example

```javascript
import { useState } from 'react';

function useAdUpdates(adId, authToken) {
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState(null);

  const updateService = new AdUpdateService('http://localhost:8000', authToken);

  const updateAd = async (updateData, isPartial = true) => {
    setIsUpdating(true);
    setUpdateError(null);

    try {
      const result = isPartial 
        ? await updateService.partialUpdateAd(adId, updateData)
        : await updateService.completeUpdateAd(adId, updateData);

      if (result.success) {
        return result.data;
      } else {
        setUpdateError(result.error);
        return null;
      }
    } catch (error) {
      setUpdateError(error.message);
      return null;
    } finally {
      setIsUpdating(false);
    }
  };

  return { updateAd, isUpdating, updateError };
}

// Component usage
function AdEditForm({ adId, currentAd }) {
  const { updateAd, isUpdating, updateError } = useAdUpdates(adId, authToken);

  const handleQuickSave = async (field, value) => {
    const updated = await updateAd({ [field]: value });
    if (updated) {
      showSuccess('Field updated successfully');
    }
  };

  // Auto-save on blur
  const handleFieldBlur = (field, value) => {
    if (value !== currentAd[field]) {
      handleQuickSave(field, value);
    }
  };

  return (
    <form>
      <input 
        defaultValue={currentAd.title}
        onBlur={e => handleFieldBlur('title', e.target.value)}
        disabled={isUpdating}
      />
      {updateError && <div className="error">{updateError}</div>}
    </form>
  );
}
```

## 🚨 Error Handling

### Common Error Responses:

**Validation Error (400):**
```json
{
  "error": "Validation failed",
  "details": {
    "starting_bid_price": ["Starting bid price must be greater than 0."],
    "reserve_price": ["Reserve price cannot be lower than starting bid price."]
  }
}
```

**Unauthorized (401):**
```json
{
  "error": "Authentication required"
}
```

**Not Found/Access Denied (404):**
```json
{
  "error": "Ad not found or you don't have permission to edit it"
}
```

**Server Error (500):**
```json
{
  "error": "Failed to update ad"
}
```

## ✅ Test Results

The update functionality has been thoroughly tested:

- ✅ **Partial Updates**: Title, description, pricing, location
- ✅ **Complete Updates**: Full ad replacement with validation
- ✅ **Validation**: Cross-field validation working correctly
- ✅ **Security**: Ownership checks and authentication
- ✅ **Error Handling**: Proper error responses and messages
- ✅ **API Endpoints**: Both PATCH and PUT methods working
- ✅ **Data Integrity**: Step calculation and completion status
- ✅ **Location Updates**: Address creation and modification

## 🎯 Use Cases

### **1. Quick Edits**
Users can quickly update individual fields:
- Fix typos in title/description
- Adjust pricing
- Update availability

### **2. Major Revisions**
Users can make comprehensive changes:
- Change material specifications
- Update processing methods
- Modify delivery options

### **3. Location Updates**
Users can update their location:
- Move to new facility
- Provide more detailed address
- Update contact information

### **4. Pricing Adjustments**
Users can adjust their auction parameters:
- Change starting bid price
- Modify reserve price
- Update currency

## 🔮 Future Enhancements

Potential improvements to consider:

1. **Version History**: Track all changes made to ads
2. **Bulk Updates**: Update multiple ads at once
3. **Scheduled Updates**: Schedule price changes or status updates
4. **Change Notifications**: Notify interested bidders of updates
5. **Update Restrictions**: Prevent updates once bidding starts
6. **Admin Overrides**: Allow admin users to update any ad

---

The ad update functionality provides complete flexibility for users to modify their material auction listings while maintaining data integrity and security. Both partial and complete update methods are available to suit different use cases and user preferences. 