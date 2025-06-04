# Postman Testing Guide - Nordic Loop Ads API

## Prerequisites

1. **Server Running**: Make sure your Django server is running on `http://localhost:8000`
2. **Authentication**: You'll need a valid user token for authentication
3. **Categories Setup**: Ensure you have categories and subcategories in your database

## Authentication Setup

First, you need to get a JWT token for authentication.

### Get JWT Token
```http
POST http://localhost:8000/api/users/login/
Content-Type: application/json

{
    "email": "test@nordicloop.com",
    "password": "testpass123"
}
```

**Response:**
```json
{
    "message": "Login successful.",
    "username": "testuser",
    "email": "test@nordicloop.com",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**For all subsequent requests, add this header:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## Complete Testing Flow

### 1. Create Material Ad with Step 1 (Material Type) - **THE STARTING POINT**

**Endpoint:** `POST /api/ads/step/1/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
    "category_id": 1,
    "subcategory_id": 1,
    "specific_material": "High-quality PP pellets for food packaging",
    "packaging": "octabin",
    "material_frequency": "quarterly"
}
```

**Expected Response:**
```json
{
    "message": "Material ad created successfully with Step 1 data. Continue with Step 2.",
    "step": 1,
    "data": {
        "id": 1,
        "category_id": 1,
        "subcategory_id": 1,
        "category_name": "Plastics",
        "subcategory_name": "PP",
        "specific_material": "High-quality PP pellets for food packaging",
        "packaging": "octabin",
        "material_frequency": "quarterly",
        "current_step": 2
    },
    "step_completion_status": {
        "1": true,
        "2": false,
        "3": false,
        "4": false,
        "5": false,
        "6": false,
        "7": false,
        "8": false
    },
    "next_incomplete_step": 2,
    "is_complete": false
}
```

**🎯 Save the `data.id` (material ID) for subsequent requests!**

---

### 2. Step 2 - Specifications

**Endpoint:** `PUT /api/ads/{material_id}/step/2/`

**Request Body:**
```json
{
    "specification_id": null,
    "additional_specifications": "Melt Flow Index: 2.5, Density: 0.95 g/cm³, Food grade certification, FDA approved"
}
```

**Expected Response:**
```json
{
    "message": "Step 2 updated successfully",
    "step": 2,
    "data": {
        "id": 1,
        "specification": null,
        "specification_id": null,
        "additional_specifications": "Melt Flow Index: 2.5, Density: 0.95 g/cm³, Food grade certification, FDA approved",
        "current_step": 3
    },
    "step_completion_status": {
        "1": true,
        "2": true,
        "3": false,
        ...
    },
    "next_incomplete_step": 3,
    "is_complete": false
}
```

---

### 3. Step 3 - Material Origin

**Endpoint:** `PUT /api/ads/{material_id}/step/3/`

**Request Body:**
```json
{
    "origin": "post_industrial"
}
```

**Expected Response:**
```json
{
    "message": "Step 3 updated successfully",
    "step": 3,
    "data": {
        "id": 1,
        "origin": "post_industrial",
        "current_step": 4
    },
    "step_completion_status": {
        "1": true,
        "2": true,
        "3": true,
        "4": false,
        ...
    },
    "next_incomplete_step": 4,
    "is_complete": false
}
```

---

### 4. Step 4 - Contamination

**Endpoint:** `PUT /api/ads/{material_id}/step/4/`

**Request Body:**
```json
{
    "contamination": "clean",
    "additives": "antioxidant",
    "storage_conditions": "climate_controlled"
}
```

**Expected Response:**
```json
{
    "message": "Step 4 updated successfully",
    "step": 4,
    "data": {
        "id": 1,
        "contamination": "clean",
        "additives": "antioxidant",
        "storage_conditions": "climate_controlled",
        "current_step": 5
    },
    "step_completion_status": {
        "1": true,
        "2": true,
        "3": true,
        "4": true,
        "5": false,
        ...
    },
    "next_incomplete_step": 5,
    "is_complete": false
}
```

---

### 5. Step 5 - Processing Methods

**Endpoint:** `PUT /api/ads/{material_id}/step/5/`

**Request Body:**
```json
{
    "processing_methods": ["extrusion", "injection_moulding", "blow_moulding"]
}
```

**Expected Response:**
```json
{
    "message": "Step 5 updated successfully",
    "step": 5,
    "data": {
        "id": 1,
        "processing_methods": ["extrusion", "injection_moulding", "blow_moulding"],
        "current_step": 6
    },
    "step_completion_status": {
        "1": true,
        "2": true,
        "3": true,
        "4": true,
        "5": true,
        "6": false,
        "7": false,
        "8": false
    },
    "next_incomplete_step": 6,
    "is_complete": false
}
```

---

### 6. Step 6 - Location & Logistics

**Endpoint:** `PUT /api/ads/{material_id}/step/6/`

**Request Body:**
```json
{
    "location_data": {
        "country": "Sweden",
        "state_province": "Stockholm County",
        "city": "Stockholm",
        "address_line": "Swedenborgsgatan 123",
        "postal_code": "12345",
        "latitude": 59.3293,
        "longitude": 18.0686
    },
    "pickup_available": true,
    "delivery_options": ["local_delivery", "pickup_only", "national_shipping"]
}
```

**Expected Response:**
```json
{
    "message": "Step 6 updated successfully",
    "step": 6,
    "data": {
        "id": 1,
        "location": {
            "id": 1,
            "country": "Sweden",
            "state_province": "Stockholm County",
            "city": "Stockholm",
            "address_line": "Swedenborgsgatan 123",
            "postal_code": "12345",
            "latitude": 59.3293,
            "longitude": 18.0686
        },
        "pickup_available": true,
        "delivery_options": ["local_delivery", "pickup_only", "national_shipping"],
        "current_step": 7
    },
    "step_completion_status": {
        "1": true,
        "2": true,
        "3": true,
        "4": true,
        "5": true,
        "6": true,
        "7": false,
        "8": false
    },
    "next_incomplete_step": 7,
    "is_complete": false
}
```

---

### 7. Step 7 - Quantity & Pricing

**Endpoint:** `PUT /api/ads/{material_id}/step/7/`

**Request Body:**
```json
{
    "available_quantity": 100,
    "unit_of_measurement": "tons",
    "minimum_order_quantity": 5,
    "starting_bid_price": 29.50,
    "currency": "EUR",
    "auction_duration": 7,
    "reserve_price": 35.00
}
```

**Expected Response:**
```json
{
    "message": "Step 7 updated successfully",
    "step": 7,
    "data": {
        "id": 1,
        "available_quantity": "100.00",
        "unit_of_measurement": "tons",
        "minimum_order_quantity": "5.00",
        "starting_bid_price": "29.50",
        "currency": "EUR",
        "auction_duration": 7,
        "reserve_price": "35.00",
        "total_starting_value": "2950.00",
        "current_step": 8
    },
    "step_completion_status": {
        "1": true,
        "2": true,
        "3": true,
        "4": true,
        "5": true,
        "6": true,
        "7": true,
        "8": false
    },
    "next_incomplete_step": 8,
    "is_complete": false
}
```

---

### 8. Step 8 - Title, Description & Image (FINAL STEP)

**Endpoint:** `PUT /api/ads/{material_id}/step/8/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
title: High-Quality PP Industrial Pellets - Food Grade
description: Premium polypropylene pellets suitable for food packaging applications. Clean, post-industrial material with excellent properties for injection molding and extrusion processes. FDA approved and food grade certified.
keywords: PP, polypropylene, food grade, industrial, pellets, FDA approved
material_image: [Upload an image file]
```

**Expected Response:**
```json
{
    "message": "Material ad completed successfully! Your material is now listed for auction.",
    "step": 8,
    "data": {
        "id": 1,
        "title": "High-Quality PP Industrial Pellets - Food Grade",
        "description": "Premium polypropylene pellets suitable for food packaging applications...",
        "keywords": "PP, polypropylene, food grade, industrial, pellets, FDA approved",
        "material_image": "/media/material_images/image.jpg",
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

---

## Additional Testing Endpoints

### Get Step Data

**Endpoint:** `GET /api/ads/{material_id}/step/{step_number}/`

**Example:** `GET /api/ads/1/step/1/`

**Expected Response:**
```json
{
    "step": 1,
    "data": {
        "id": 1,
        "category_id": 1,
        "subcategory_id": 1,
        "category_name": "Plastics",
        "subcategory_name": "PP",
        "specific_material": "High-quality PP pellets for food packaging",
        "packaging": "octabin",
        "material_frequency": "quarterly",
        "current_step": 8
    },
    "step_completion_status": {
        "1": true,
        "2": true,
        ...
    },
    "next_incomplete_step": null
}
```

### Validate Step Data

**Endpoint:** `POST /api/ads/validate/step/{step_number}/`

**Example:** `POST /api/ads/validate/step/1/`

**Request Body:**
```json
{
    "category_id": 1,
    "subcategory_id": 1,
    "packaging": "octabin",
    "material_frequency": "quarterly"
}
```

**Expected Response:**
```json
{
    "valid": true,
    "message": "Step 1 data is valid"
}
```

### Get Complete Material Details

**Endpoint:** `GET /api/ads/{material_id}/`

**Expected Response:**
```json
{
    "id": 1,
    "user": 1,
    "category_name": "Plastics",
    "subcategory_name": "PP",
    "specific_material": "High-quality PP pellets for food packaging",
    "packaging": "octabin",
    "material_frequency": "quarterly",
    "specification": null,
    "additional_specifications": "Melt Flow Index: 2.5...",
    "origin": "post_industrial",
    "contamination": "clean",
    "additives": "antioxidant",
    "storage_conditions": "climate_controlled",
    "processing_methods": ["extrusion", "injection_moulding"],
    "location": {
        "id": 1,
        "country": "Sweden",
        "city": "Stockholm",
        ...
    },
    "pickup_available": true,
    "delivery_options": ["local_delivery", "pickup_only"],
    "available_quantity": "100.00",
    "starting_bid_price": "29.50",
    "currency": "EUR",
    "total_starting_value": "2950.00",
    "title": "High-Quality PP Industrial Pellets - Food Grade",
    "description": "Premium polypropylene pellets...",
    "material_image": "/media/material_images/image.jpg",
    "is_active": false,
    "current_step": 8,
    "is_complete": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:00:00Z",
    "step_completion_status": {
        "1": true,
        "2": true,
        "3": true,
        "4": true,
        "5": true,
        "6": true,
        "7": true,
        "8": true
    }
}
```

### List All Materials

**Endpoint:** `GET /api/ads/`

**Query Parameters:**
- `category=1` - Filter by category
- `origin=post_industrial` - Filter by origin
- `country=Sweden` - Filter by country
- `complete=true` - Only complete materials

**Example:** `GET /api/ads/?category=1&origin=post_industrial&complete=true`

### List User's Materials

**Endpoint:** `GET /api/ads/user/`

**Query Parameters:**
- `complete=true` - Only complete materials
- `complete=false` - Include draft materials

**Example:** `GET /api/ads/user/?complete=false`

### Delete Material

**Endpoint:** `DELETE /api/ads/{material_id}/`

**Expected Response:**
```json
{
    "message": "Ad deleted successfully"
}
```

---

## Testing Scenarios

### 1. Happy Path (Complete Flow)
1. **Create material with Step 1** → Get material ID
2. **Complete steps 2-8** in sequence using the material ID
3. **Verify material is complete**
4. **Retrieve complete material details**

### 2. Validation Testing
- Test with invalid category IDs
- Test with missing required fields
- Test with invalid data types
- Test step validation endpoint

### 3. Error Handling
- Test unauthorized access
- Test accessing non-existent materials
- Test invalid step numbers
- Test incomplete data submissions

### 4. Permission Testing
- Try to access another user's material
- Try to edit another user's material
- Test authentication requirements

### 5. Data Integrity
- Test minimum/maximum values
- Test reserve price vs starting price validation
- Test quantity validations

---

## Common Choice Values

### Packaging Options:
- `baled`
- `loose` 
- `big_bag`
- `octabin`
- `roles`
- `container`
- `other`

### Material Frequency:
- `one_time`
- `weekly`
- `bi_weekly`
- `monthly`
- `quarterly`
- `yearly`

### Origin:
- `post_industrial`
- `post_consumer`
- `mix`

### Contamination:
- `clean`
- `slightly_contaminated`
- `heavily_contaminated`

### Additives:
- `uv_stabilizer`
- `antioxidant`
- `flame_retardants`
- `chlorides`
- `no_additives`

### Storage Conditions:
- `climate_controlled`
- `protected_outdoor`
- `unprotected_outdoor`

### Processing Methods:
- `blow_moulding`
- `injection_moulding`
- `extrusion`
- `calendering`
- `rotational_moulding`
- `sintering`
- `thermoforming`

### Delivery Options:
- `pickup_only`
- `local_delivery`
- `national_shipping`
- `international_shipping`
- `freight_forwarding`

### Currency:
- `EUR`
- `USD`
- `SEK`
- `GBP`

### Unit of Measurement:
- `kg`
- `g`
- `lb`
- `tons`

---

## Quick Start Guide Summary

1. **Login:** `POST /api/users/login/` → Get access token
2. **Create Material:** `POST /api/ads/step/1/` → Get material ID
3. **Complete Steps:** `PUT /api/ads/{material_id}/step/{2-8}/` → Update each step
4. **Verify:** `GET /api/ads/{material_id}/` → Check complete material

## Tips for Testing

1. **Save material_id**: Always save the material ID from step 1 response
2. **Check current_step**: Notice how it increments after each step
3. **Monitor step_completion_status**: Track progress through the object
4. **Test validation**: Use the validation endpoint before submitting
5. **File uploads**: For step 8, use multipart/form-data for images
6. **Authentication**: Always include the Bearer token in headers
7. **Error responses**: Check error messages for debugging

This provides a more intuitive workflow where creating the material and defining its type happens in one step! 