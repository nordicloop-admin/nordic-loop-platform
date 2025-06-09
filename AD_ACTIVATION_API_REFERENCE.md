# Ad Activation API Reference

## Overview

This document provides the exact request and response formats for the ad activation/publishing endpoints.

---

## 1. Activate Ad (Publish)

### Endpoint
```
POST /api/ads/{ad_id}/activate/
```

### Description
Activate/publish a completed ad to make it visible and available for bidding.

### Requirements
- User must be authenticated
- User must own the ad
- Ad must be `is_complete=true`

### Request Format
```http
POST /api/ads/{ad_id}/activate/
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN
```

**Note:** No request body is required.

### Example Request
```bash
curl -X POST \
  "http://localhost:8000/api/ads/45/activate/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

### Success Response (HTTP 200)
```json
{
  "message": "Ad activated successfully and is now live for auction",
  "ad": {
    "id": 45,
    "title": "High-Quality HDPE Bottles - Food Grade",
    "is_active": true,
    "is_complete": true,
    "auction_start_date": "2024-06-08T14:30:45.123Z",
    "auction_end_date": "2024-06-15T14:30:45.123Z",
    "auction_duration_display": "7 days"
  }
}
```

### Error Responses

#### Ad Not Complete (HTTP 400)
```json
{
  "error": "Ad must be complete before activation"
}
```

#### Ad Not Found or No Permission (HTTP 400)
```json
{
  "error": "Ad not found or access denied"
}
```

#### Already Active (HTTP 400)
```json
{
  "error": "Ad is already active"
}
```

#### Server Error (HTTP 500)
```json
{
  "error": "Failed to activate ad"
}
```

---

## 2. Deactivate Ad (Unpublish)

### Endpoint
```
POST /api/ads/{ad_id}/deactivate/
```

### Description
Deactivate/unpublish an ad to make it invisible and stop bidding.

### Requirements
- User must be authenticated
- User must own the ad

### Request Format
```http
POST /api/ads/{ad_id}/deactivate/
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN
```

**Note:** No request body is required.

### Example Request
```bash
curl -X POST \
  "http://localhost:8000/api/ads/45/deactivate/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

### Success Response (HTTP 200)
```json
{
  "message": "Ad deactivated successfully and is no longer visible for bidding",
  "ad": {
    "id": 45,
    "title": "High-Quality HDPE Bottles - Food Grade",
    "is_active": false,
    "is_complete": true
  }
}
```

### Error Responses

#### Ad Not Found or No Permission (HTTP 400)
```json
{
  "error": "Ad not found or access denied"
}
```

#### Server Error (HTTP 500)
```json
{
  "error": "Failed to deactivate ad"
}
```

---

## JavaScript Integration Examples

### Basic Fetch API
```javascript
// Activate Ad
const activateAd = async (adId, token) => {
  const response = await fetch(`/api/ads/${adId}/activate/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (response.ok) {
    const data = await response.json();
    console.log('Success:', data.message);
    console.log('Auction ends:', data.ad.auction_end_date);
    return data;
  } else {
    const error = await response.json();
    throw new Error(error.error);
  }
};

// Deactivate Ad
const deactivateAd = async (adId, token) => {
  const response = await fetch(`/api/ads/${adId}/deactivate/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (response.ok) {
    const data = await response.json();
    console.log('Success:', data.message);
    return data;
  } else {
    const error = await response.json();
    throw new Error(error.error);
  }
};
```

### React Hook
```jsx
import { useState } from 'react';

const useAdActivation = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const activateAd = async (adId) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/ads/${adId}/activate/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error);
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const deactivateAd = async (adId) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/ads/${adId}/deactivate/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error);
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  return { activateAd, deactivateAd, loading, error };
};
```

### React Component Usage
```jsx
const AdManagement = ({ ad }) => {
  const { activateAd, deactivateAd, loading, error } = useAdActivation();
  
  const handleActivate = async () => {
    try {
      const result = await activateAd(ad.id);
      alert(`Ad activated! Auction ends: ${result.ad.auction_end_date}`);
      // Refresh ad data or update state
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };
  
  const handleDeactivate = async () => {
    try {
      const result = await deactivateAd(ad.id);
      alert(result.message);
      // Refresh ad data or update state
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };
  
  return (
    <div>
      {ad.is_complete && !ad.is_active && (
        <button onClick={handleActivate} disabled={loading}>
          {loading ? 'Publishing...' : '🚀 Publish Ad'}
        </button>
      )}
      
      {ad.is_active && (
        <button onClick={handleDeactivate} disabled={loading}>
          {loading ? 'Unpublishing...' : '⏸️ Unpublish Ad'}
        </button>
      )}
      
      {error && <div className="error">{error}</div>}
    </div>
  );
};
```

---

## Python Integration Example

```python
import requests

def activate_ad(ad_id, token):
    """Activate an ad for auction."""
    url = f"http://localhost:8000/api/ads/{ad_id}/activate/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['message']}")
        print(f"Auction ends: {data['ad']['auction_end_date']}")
        return data
    else:
        error = response.json()
        print(f"Error: {error['error']}")
        return None

def deactivate_ad(ad_id, token):
    """Deactivate an ad."""
    url = f"http://localhost:8000/api/ads/{ad_id}/deactivate/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['message']}")
        return data
    else:
        error = response.json()
        print(f"Error: {error['error']}")
        return None

# Usage example
if __name__ == "__main__":
    token = "your_jwt_token_here"
    ad_id = 45
    
    # Activate ad
    result = activate_ad(ad_id, token)
    if result:
        print("Ad successfully activated!")
    
    # Later, deactivate ad
    result = deactivate_ad(ad_id, token)
    if result:
        print("Ad successfully deactivated!")
```

---

## Testing Examples

### Real Test Data
Based on current database, you can test with:

```bash
# Test Activation (Replace with your actual JWT token)
curl -X POST \
  "http://localhost:8000/api/ads/122/activate/" \
  -H "Authorization: Bearer YOUR_ACTUAL_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Expected Response:
{
  "message": "Ad activated successfully and is now live for auction",
  "ad": {
    "id": 122,
    "title": "Organic waste - Grass and leaves from green maintenance",
    "is_active": true,
    "is_complete": true,
    "auction_start_date": "2024-06-08T15:45:30.123Z",
    "auction_end_date": "2024-06-15T15:45:30.123Z",
    "auction_duration_display": "7 days"
  }
}
```

### Postman Collection
```json
{
  "info": {
    "name": "Ad Activation API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Activate Ad",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{jwt_token}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "url": {
          "raw": "{{base_url}}/api/ads/{{ad_id}}/activate/",
          "host": ["{{base_url}}"],
          "path": ["api", "ads", "{{ad_id}}", "activate", ""]
        }
      }
    },
    {
      "name": "Deactivate Ad",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{jwt_token}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "url": {
          "raw": "{{base_url}}/api/ads/{{ad_id}}/deactivate/",
          "host": ["{{base_url}}"],
          "path": ["api", "ads", "{{ad_id}}", "deactivate", ""]
        }
      }
    }
  ]
}
```

---

## What Happens Behind the Scenes

### Activation Process
1. **Validation**: Check if ad exists, user owns it, and ad is complete
2. **Set Status**: `is_active = true`
3. **Set Dates**: 
   - `auction_start_date = now()`
   - `auction_end_date = start_date + duration`
4. **Save**: Persist changes to database
5. **Response**: Return updated ad information

### Deactivation Process
1. **Validation**: Check if ad exists and user owns it
2. **Set Status**: `is_active = false`
3. **Preserve Data**: Keep all existing data (bids, dates, etc.)
4. **Save**: Persist changes to database
5. **Response**: Return updated ad information

---

## Key Points

- ✅ **No Request Body Required** - Both endpoints just need the ad ID in the URL
- 🔐 **Authentication Required** - Must include valid JWT token in Authorization header
- 👤 **Owner-Only Access** - Can only activate/deactivate your own ads
- ⚡ **Immediate Effect** - Activation sets auction dates and makes ad visible instantly
- 🔄 **Reversible** - Can activate/deactivate multiple times as needed
- 💾 **Data Preservation** - Deactivation keeps all ad and bid data intact 