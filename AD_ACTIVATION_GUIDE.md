# Ad Activation/Publishing API Guide

## Overview

This guide covers the new ad activation/publishing endpoints that control when ads become visible and available for bidding on the marketplace.

## Ad Lifecycle States

| State | is_complete | is_active | Visible To | Can Receive Bids | Auction Status |
|-------|-------------|-----------|------------|------------------|----------------|
| **Draft** | `false` | `false` | Owner only | ❌ No | Not Started |
| **Completed (Private)** | `true` | `false` | Owner only | ❌ No | Not Started |
| **Published (Live)** | `true` | `true` | Everyone | ✅ Yes | Active/Scheduled |

## Endpoints

### 1. Activate Ad (Publish)

**Endpoint:** `POST /api/ads/{ad_id}/activate/`

**Purpose:** Activate/publish a completed ad to make it visible and available for bidding.

**Requirements:**
- User must be authenticated
- User must own the ad
- Ad must be `is_complete=true`

**Request:**
```bash
curl -X POST \
  "http://localhost:8000/api/ads/123/activate/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Success Response (200):**
```json
{
  "message": "Ad activated successfully and is now live for auction",
  "ad": {
    "id": 123,
    "title": "High-Quality HDPE Bottles",
    "is_active": true,
    "is_complete": true,
    "auction_start_date": "2024-06-08T14:30:00Z",
    "auction_end_date": "2024-06-15T14:30:00Z",
    "auction_duration_display": "7 days"
  }
}
```

**Error Responses:**
```json
// Ad not complete
{
  "error": "Ad must be complete before activation"
}

// Not found or no permission
{
  "error": "Ad not found or access denied"
}

// Already active
{
  "error": "Ad is already active"
}
```

### 2. Deactivate Ad (Unpublish)

**Endpoint:** `POST /api/ads/{ad_id}/deactivate/`

**Purpose:** Deactivate/unpublish an ad to make it invisible and stop bidding.

**Requirements:**
- User must be authenticated
- User must own the ad

**Request:**
```bash
curl -X POST \
  "http://localhost:8000/api/ads/123/deactivate/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Success Response (200):**
```json
{
  "message": "Ad deactivated successfully and is no longer visible for bidding",
  "ad": {
    "id": 123,
    "title": "High-Quality HDPE Bottles",
    "is_active": false,
    "is_complete": true
  }
}
```

## What Happens When You Activate an Ad

1. **Set Active Status:** `is_active = true`
2. **Set Auction Start:** `auction_start_date = now()`
3. **Calculate End Date:** `auction_end_date = start_date + duration`
4. **Make Visible:** Ad appears in public marketplace listings
5. **Enable Bidding:** Users can now place bids on the ad

## What Happens When You Deactivate an Ad

1. **Set Inactive Status:** `is_active = false`
2. **Hide from Public:** Ad no longer appears in marketplace listings
3. **Stop Bidding:** No new bids can be placed
4. **Preserve Data:** Existing bids and ad data remain intact

## Frontend Integration

### React Example

```javascript
const activateAd = async (adId) => {
  try {
    const response = await fetch(`/api/ads/${adId}/activate/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('Ad activated:', data.ad);
      // Update UI to show ad as active
      setAdStatus('active');
      setAuctionDates({
        start: data.ad.auction_start_date,
        end: data.ad.auction_end_date
      });
    } else {
      const error = await response.json();
      console.error('Activation failed:', error.error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};

const deactivateAd = async (adId) => {
  try {
    const response = await fetch(`/api/ads/${adId}/deactivate/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('Ad deactivated:', data.ad);
      // Update UI to show ad as inactive
      setAdStatus('inactive');
    }
  } catch (error) {
    console.error('Deactivation failed:', error);
  }
};
```

### UI Implementation Suggestions

1. **Ad Dashboard Button:**
   ```jsx
   {ad.is_complete && !ad.is_active && (
     <button onClick={() => activateAd(ad.id)} className="btn-primary">
       🚀 Publish Ad
     </button>
   )}
   
   {ad.is_active && (
     <button onClick={() => deactivateAd(ad.id)} className="btn-secondary">
       ⏸️ Unpublish Ad
     </button>
   )}
   ```

2. **Status Indicators:**
   ```jsx
   const getStatusBadge = (ad) => {
     if (!ad.is_complete) return <Badge color="gray">Draft</Badge>;
     if (!ad.is_active) return <Badge color="orange">Ready to Publish</Badge>;
     return <Badge color="green">Live Auction</Badge>;
   };
   ```

## Business Rules

1. **Only completed ads can be activated** (all 8 steps must be filled)
2. **Only ad owners can activate/deactivate their ads**
3. **Activation sets auction start/end dates automatically**
4. **Deactivation preserves all ad data and existing bids**
5. **Ads can be reactivated after deactivation** (with new auction dates)

## Use Cases

### For Sellers:
- **Control timing:** Publish ads when ready to handle inquiries
- **Manage inventory:** Deactivate when material is no longer available
- **Market strategy:** Time releases based on market conditions

### For Platform:
- **Quality control:** Ensure only complete ads are visible
- **User experience:** Clean marketplace with active auctions only
- **Data integrity:** Preserve all information for reactivation

## Testing

Test with an existing completed ad:

```bash
# Get your user ads to find a completed one
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/ads/user/?complete=true"

# Activate a specific ad
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/ads/REPLACE_WITH_AD_ID/activate/"

# Check the ad status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/ads/REPLACE_WITH_AD_ID/"
```

This gives sellers full control over when their ads go live and provides a clean separation between draft/ready and published states. 