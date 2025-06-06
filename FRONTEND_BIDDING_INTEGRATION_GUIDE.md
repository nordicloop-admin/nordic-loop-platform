# 📋 Nordic Loop Bidding System - Frontend Integration Guide

This guide provides comprehensive instructions for integrating with the enhanced bidding system API.

## 🔐 Authentication Requirements

All bidding endpoints require JWT authentication. Include the access token in the Authorization header:

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

## 🎯 Creating Bids Workflow

### Step 1: Validate Ad Eligibility
Before allowing users to bid, check:
- User is not the ad owner
- Ad is active and auction hasn't ended
- Starting bid price and available quantity

### Step 2: Create Bid

**Endpoint:** `POST /api/bids/create/`

**Required Fields:**
```javascript
{
  "ad": 11,                          // Ad ID (required)
  "bid_price_per_unit": "55.00",     // Bid price per unit (required)
  "volume_requested": "25.00",       // Volume requested (required)
  "volume_type": "partial",          // "partial" or "full" (optional, defaults to "partial")
  "notes": "Interested in this material", // Optional notes
  "max_auto_bid_price": "65.00"      // Auto-bidding max price (optional)
}
```

**Success Response (201):**
```javascript
{
  "message": "Bid placed successfully",
  "bid": {
    "id": 25,
    "bidder_name": "jane_buyer",
    "ad_title": "Premium HDPE Material",
    "bid_price_per_unit": "55.00",
    "volume_requested": "25.00",
    "total_bid_value": "1375.00",
    "currency": "EUR",
    "unit": "tons",
    "status": "active",
    "is_winning": true,
    "rank": 1,
    "volume_type": "partial",
    "is_auto_bid": true,
    "max_auto_bid_price": "65.00",
    "notes": "Interested in this material",
    "created_at": "2025-06-06T12:00:00Z",
    "updated_at": "2025-06-06T12:00:00Z"
  }
}
```

**Error Response (400):**
```javascript
{
  "error": "Invalid bid data",
  "details": {
    "bid_price_per_unit": ["Bid price must be at least 50.00 EUR"],
    "volume_requested": ["Volume cannot exceed available quantity"]
  }
}
```

### Step 3: Handle Business Logic Validations

The API automatically validates:
- ✅ Bid price >= starting bid price
- ✅ Volume <= available quantity  
- ✅ User != ad owner
- ✅ Ad is active
- ✅ Auto-bid price > current bid price

## 🔄 Updating Bids Workflow

### Step 1: Check Update Eligibility
- User can only update their own bids
- Bid must be active (not cancelled/won/lost)
- New price must be higher than current highest bid

### Step 2: Update Bid

**Endpoint:** `PUT /api/bids/{bid_id}/update/`

**Request Body (partial updates allowed):**
```javascript
{
  "bid_price_per_unit": "60.00",     // New bid price
  "volume_requested": "30.00",       // New volume (optional)
  "notes": "Updated my bid",         // Updated notes (optional)
  "max_auto_bid_price": "70.00"      // New auto-bid limit (optional)
}
```

**Success Response (200):**
```javascript
{
  "message": "Bid updated successfully",
  "bid": {
    "id": 25,
    "bidder_name": "jane_buyer",
    "ad_title": "Premium HDPE Material",
    "bid_price_per_unit": "60.00",    // Updated price
    "volume_requested": "30.00",      // Updated volume
    "total_bid_value": "1800.00",     // Recalculated
    "currency": "EUR",
    "unit": "tons",
    "status": "winning",
    "is_winning": true,
    "rank": 1,
    "notes": "Updated my bid",
    "created_at": "2025-06-06T12:00:00Z",
    "updated_at": "2025-06-06T12:05:00Z"  // Updated timestamp
  }
}
```

**Important:** Updates automatically create bid history entries for audit trail.

## 📋 Listing and Viewing Bids

### 1. View All Platform Bids
**Endpoint:** `GET /api/bids/`

**Optional Query Parameters:**
- `status` - Filter by bid status (active, winning, outbid, won, lost, cancelled)
- `ad_id` - Filter by specific ad ID
- `page` - Pagination

**Response:**
```javascript
{
  "count": 25,
  "next": "http://localhost:8000/api/bids/?page=2",
  "previous": null,
  "results": [
    {
      "id": 25,
      "bidder_name": "jane_buyer",
      "ad_title": "Premium HDPE Material",
      "bid_price_per_unit": "60.00",
      "volume_requested": "30.00",
      "total_bid_value": "1800.00",
      "currency": "EUR",
      "unit": "tons",
      "status": "winning",
      "is_winning": true,
      "rank": 1,
      "created_at": "2025-06-06T12:00:00Z"
    }
    // ... more bids
  ],
  "page_size": 10,
  "total_pages": 3,
  "current_page": 1,
  "platform_statistics": {
    "total_bids": 25,
    "active_bids": 18,
    "total_bidders": 12
  }
}
```

### 2. View Bids for Specific Ad
**Endpoint:** `GET /api/bids/ad/{ad_id}/`

**Response includes bid statistics and ad information:**
```javascript
{
  "count": 5,
  "results": [
    // ... bid objects sorted by price (highest first)
  ],
  "bid_statistics": {
    "total_bids": 5,
    "highest_bid": 65.0,
    "lowest_bid": 50.0,
    "average_bid": 57.5,
    "total_volume_requested": 125.0,
    "unique_bidders": 4
  },
  "ad_info": {
    "id": 11,
    "title": "Premium HDPE Material",
    "starting_bid_price": 45.0,
    "reserve_price": 70.0,
    "available_quantity": 100.0,
    "currency": "EUR",
    "auction_end_date": "2025-06-13T19:45:25Z"
  }
}
```

### 3. View User's Own Bids
**Endpoint:** `GET /api/bids/user/`

**Optional Query Parameters:**
- `status` - Filter by status

### 4. View User's Winning Bids
**Endpoint:** `GET /api/bids/user/winning/`

### 5. Search Bids
**Endpoint:** `GET /api/bids/search/`

**Query Parameters:**
- `ad_title` - Search by ad title
- `category` - Filter by material category
- `min_price` - Minimum bid price
- `max_price` - Maximum bid price
- `status` - Bid status
- `user_id` - Specific user's bids

## 🗑️ Cancelling Bids

**Endpoint:** `DELETE /api/bids/{bid_id}/delete/`

**Success Response (200):**
```javascript
{
  "message": "Bid cancelled successfully"
}
```

**Note:** This sets bid status to 'cancelled' rather than deleting the record.

## 📊 Getting Bid Statistics

**Endpoint:** `GET /api/bids/ad/{ad_id}/stats/`

**Response:**
```javascript
{
  "total_bids": 5,
  "highest_bid": 65.0,
  "lowest_bid": 50.0,
  "average_bid": 57.5,
  "total_volume_requested": 125.0,
  "unique_bidders": 4,
  "current_highest_bid": {
    "bid_price_per_unit": 65.0,
    "total_bid_value": 1950.0,
    "volume_requested": 30.0,
    "bidder": "mike_buyer",
    "timestamp": "2025-06-06T12:00:00Z"
  }
}
```

## 📈 Bid History and Audit Trail

**Endpoint:** `GET /api/bids/{bid_id}/history/`

**Response:**
```javascript
[
  {
    "id": 15,
    "previous_price": "55.00",
    "new_price": "60.00",
    "previous_volume": "25.00",
    "new_volume": "30.00",
    "change_reason": "bid_updated",
    "timestamp": "2025-06-06T12:05:00Z"
  },
  {
    "id": 14,
    "previous_price": null,
    "new_price": "55.00",
    "previous_volume": null,
    "new_volume": "25.00",
    "change_reason": "bid_placed",
    "timestamp": "2025-06-06T12:00:00Z"
  }
]
```

## 🎭 Bid Status Management

**Bid Statuses:**
- `active` - Bid is active but not currently winning
- `winning` - Currently the highest bid
- `outbid` - Was winning but now outbid by another user
- `won` - Won the auction (final status)
- `lost` - Lost the auction (final status)
- `cancelled` - User cancelled their bid

**Status Transitions:**
```
active → winning → won ✅
active → outbid → winning → won ✅
active → cancelled ❌
winning → outbid → lost ❌
```

## 🚀 Auto-Bidding Feature

When creating/updating bids with `max_auto_bid_price`:

1. **System automatically bids** when user is outbid
2. **Bids up to the maximum** price specified
3. **Creates bid history** for each auto-bid
4. **Stops at maximum** - won't exceed limit

**Frontend Implementation Tips:**
- Show auto-bid toggle in UI
- Display current max auto-bid price
- Allow users to increase max price
- Show auto-bid activity in notifications

## ⚠️ Error Handling

**Common Error Codes:**
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (permission denied)
- `404` - Not Found (bid/ad doesn't exist)
- `500` - Server Error

**Frontend Error Handling Strategy:**
```javascript
try {
  const response = await fetch('/api/bids/create/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(bidData)
  });
  
  const result = await response.json();
  
  if (response.ok) {
    // Success - show bid confirmation
    showSuccessMessage(result.message);
    updateBidList(result.bid);
  } else {
    // Error - show validation messages
    showErrorMessages(result.details || result.error);
  }
} catch (error) {
  // Network/server error
  showErrorMessage('Connection error. Please try again.');
}
```

## 🔔 Real-time Updates Recommendations

**For optimal UX, implement:**

1. **Polling for bid updates** every 30-60 seconds on active auction pages
2. **WebSocket connections** for real-time bid notifications
3. **Status indicators** showing current bid position
4. **Auto-refresh** when user is outbid
5. **Push notifications** for important bid events

## 📱 Mobile Considerations

**Key mobile optimizations:**
- **Quick bid buttons** (+€5, +€10, +€20)
- **Swipe to refresh** bid lists
- **Simplified forms** with smart defaults
- **Offline bid caching** for poor connectivity
- **Touch-friendly** volume sliders

## 🧪 Testing Endpoints

Use the sample data created by running:
```bash
python create_sample_bids.py
```

This creates bids across multiple ads with different scenarios for testing.

## 📋 Complete API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/bids/` | List all bids (platform-wide) |
| `POST` | `/api/bids/create/` | Create new bid |
| `GET` | `/api/bids/{bid_id}/` | Get bid details |
| `PUT` | `/api/bids/{bid_id}/update/` | Update existing bid |
| `DELETE` | `/api/bids/{bid_id}/delete/` | Cancel bid |
| `GET` | `/api/bids/{bid_id}/history/` | Get bid history |
| `GET` | `/api/bids/ad/{ad_id}/` | List bids for specific ad |
| `GET` | `/api/bids/ad/{ad_id}/stats/` | Get bid statistics for ad |
| `POST` | `/api/bids/ad/{ad_id}/close/` | Close auction (ad owners only) |
| `GET` | `/api/bids/user/` | Get current user's bids |
| `GET` | `/api/bids/user/winning/` | Get user's winning bids |
| `GET` | `/api/bids/search/` | Search bids with filters |

## 🏗️ Frontend UI Component Suggestions

### 1. Bid Creation Form
```javascript
// Key form fields to include:
- Bid amount input (with currency display)
- Volume slider/input (show available quantity)
- Volume type toggle (partial/full)
- Auto-bid toggle with max price input
- Notes textarea
- Submit button with validation
```

### 2. Bid List Component
```javascript
// Display elements:
- Bid ranking badges (#1, #2, etc.)
- Status indicators (Winning, Outbid, etc.)
- Price and volume information
- Time remaining countdown
- Quick action buttons (Update, Cancel)
```

### 3. Ad Detail Bidding Section
```javascript
// Key elements:
- Current highest bid display
- Bid statistics summary
- Quick bid buttons
- Bid history timeline
- Your current bid status
```

### 4. Real-time Notifications
```javascript
// Notification types:
- "You've been outbid!"
- "Your auto-bid activated"
- "Auction ending soon"
- "You won the auction!"
- "Bid placed successfully"
```

---

This bidding system provides a complete auction experience with auto-bidding, comprehensive tracking, and robust business logic validation. The API is designed to handle high-volume bidding scenarios while maintaining data integrity and user experience.

**Contact Backend Developer:** If you need any clarification or encounter issues, please reach out with specific error messages and request/response examples. 