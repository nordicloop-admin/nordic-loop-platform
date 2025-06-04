# Nordic Loop Platform - Ads Module

## 8-Step Material Ad Creation System

This module implements a comprehensive 8-step material listing system for the Nordic Loop marketplace platform. Users can create detailed material ads through a guided step-by-step process.

## Overview

The system allows users to list materials for auction by completing 8 distinct steps:

1. **Material Type** - Basic material categorization and packaging
2. **Specifications** - Detailed material specifications
3. **Material Origin** - Source of the material (post-industrial, post-consumer, mix)
4. **Contamination** - Contamination level and storage conditions
5. **Processing Methods** - Applicable processing methods
6. **Location & Logistics** - Material location and delivery options
7. **Quantity & Pricing** - Auction pricing and quantities
8. **Title, Description & Image** - Final listing details

## API Endpoints

### Create New Ad
```
POST /api/ads/create/
```
Creates a new empty ad and returns the ad ID for step-by-step completion.

**Response:**
```json
{
    "message": "Ad created successfully. Continue with step 1.",
    "ad": {
        "id": 1,
        "user": 1,
        "current_step": 1
    }
}
```

### Update Step
```
PUT /api/ads/{ad_id}/step/{step}/
```
Updates a specific step of the ad. Steps 1-8 are supported.

**Step 1 Example (Material Type):**
```json
{
    "category_id": 1,
    "subcategory_id": 2,
    "specific_material": "Grade 5052 Aluminum pellets",
    "packaging": "octabin",
    "material_frequency": "quarterly"
}
```

**Step 7 Example (Quantity & Pricing):**
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

### Get Step Data
```
GET /api/ads/{ad_id}/step/{step}/
```
Retrieves current data for a specific step.

### Validate Step Data
```
POST /api/ads/validate/step/{step}/
```
Validates step data without saving it.

### List Ads
```
GET /api/ads/
```
Lists all active and complete ads with optional filtering.

**Query Parameters:**
- `category` - Filter by category ID
- `subcategory` - Filter by subcategory ID
- `origin` - Filter by material origin
- `contamination` - Filter by contamination level
- `country` - Filter by location country
- `city` - Filter by location city
- `complete` - Only show complete ads (default: true)

### User's Ads
```
GET /api/ads/user/
```
Lists current user's ads (both complete and in-progress).

### Ad Details
```
GET /api/ads/{ad_id}/
```
Get complete ad details.

### Delete Ad
```
DELETE /api/ads/{ad_id}/
```
Delete an ad (only by owner).

## Models

### Ad Model
The main Ad model contains all fields for the 8 steps:

- **Step 1 Fields:** category, subcategory, specific_material, packaging, material_frequency
- **Step 2 Fields:** specification, additional_specifications
- **Step 3 Fields:** origin
- **Step 4 Fields:** contamination, additives, storage_conditions
- **Step 5 Fields:** processing_methods (JSON array)
- **Step 6 Fields:** location (FK), pickup_available, delivery_options (JSON array)
- **Step 7 Fields:** available_quantity, starting_bid_price, currency, auction_duration, reserve_price
- **Step 8 Fields:** title, description, keywords, material_image

### Location Model
Separate model for detailed location information:
- country, state_province, city, address_line, postal_code
- latitude, longitude (for mapping)

## Step Validation Rules

### Step 1 - Material Type
- Category and subcategory are required
- Subcategory must belong to selected category
- Packaging and material frequency are required

### Step 2 - Specifications
- Optional step - specification can be linked or additional specs provided

### Step 3 - Material Origin
- Origin selection is required (post_industrial, post_consumer, mix)

### Step 4 - Contamination
- All fields required: contamination level, additives, storage conditions

### Step 5 - Processing Methods
- At least one processing method must be selected
- Multiple methods allowed (stored as JSON array)

### Step 6 - Location & Logistics
- Location details required (creates/updates Location model)
- At least one delivery option must be selected

### Step 7 - Quantity & Pricing
- Available quantity and starting bid price are required
- Minimum order quantity cannot exceed available quantity
- Reserve price cannot be lower than starting bid price

### Step 8 - Title, Description & Image
- Title must be at least 10 characters
- Description must be at least 50 characters
- Completing this step marks the ad as complete (`is_complete = True`)

## Progress Tracking

Each ad tracks its completion status:

- `current_step` - Current step number (1-8)
- `is_complete` - Whether all steps are completed
- `step_completion_status` - Dynamic property showing completion status for each step

## Example Usage Flow

1. **Create Ad:**
   ```bash
   POST /api/ads/create/
   # Returns ad_id
   ```

2. **Complete Step 1:**
   ```bash
   PUT /api/ads/{ad_id}/step/1/
   {
       "category_id": 1,
       "subcategory_id": 2,
       "packaging": "octabin",
       "material_frequency": "quarterly"
   }
   ```

3. **Continue through steps 2-7...**

4. **Complete Step 8:**
   ```bash
   PUT /api/ads/{ad_id}/step/8/
   {
       "title": "High-Quality PP Pellets - Food Grade",
       "description": "Premium polypropylene pellets...",
       "keywords": "PP, food grade, pellets"
   }
   # Ad is now complete and ready for auction
   ```

## Material Categories

The system supports various material categories:
- Plastics (PP, HDPE, PET, etc.)
- Paper (various types)
- Metals (aluminum, steel, etc.)
- Glass
- Textiles
- Wood
- Building materials
- E-waste
- Organic waste
- Chemical substances

## Features

- **Step-by-step validation** - Each step is validated independently
- **Progress tracking** - Users can see completion status
- **Draft saving** - Ads are saved at each step
- **Owner permissions** - Only ad owners can edit their ads
- **Rich filtering** - Multiple filter options for ad discovery
- **Location-based search** - Find materials by geographic location
- **Auction integration** - Ready for bidding system integration

## Security

- Authentication required for all operations
- Users can only edit their own ads
- Input validation on all fields
- SQL injection protection via Django ORM
- File upload validation for images

## Performance

- Database indexing on frequently queried fields
- Efficient queries with select_related/prefetch_related
- Pagination support for large datasets
- Optimized serializers for different use cases

## Testing

Comprehensive test suite covering:
- Model functionality and validation
- API endpoints and authentication
- Step-by-step workflow
- Data validation and error handling
- Permission checks

Run tests with:
```bash
python manage.py test ads
``` 