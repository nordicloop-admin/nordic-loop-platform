# Company Search and Filter API Documentation

## Overview
The Companies page now supports comprehensive search and filter functionality for both company information and associated user names.

## Endpoints

### 1. Get Filter Options
**GET** `/api/company/filters/`

Returns available filter options for dropdowns.

**Response:**
```json
{
  "sectors": [
    {"value": "manufacturing  & Production", "label": "Manufacturing & Production"},
    {"value": "construction", "label": "Construction & Demolition"},
    // ... more sectors
  ],
  "countries": [
    {"value": "Sweden", "label": "Sweden"},
    {"value": "US", "label": "US"},
    // ... more countries
  ],
  "statuses": [
    {"value": "pending", "label": "Pending Approval"},
    {"value": "approved", "label": "Approved"},
    {"value": "rejected", "label": "Rejected"}
  ]
}
```

### 2. Search and Filter Companies
**GET** `/api/company/admin/companies/`

**Authentication:** Required (Admin users only)

**Query Parameters:**
- `search` (string, optional): Search term for company name, VAT number, email, country, or associated user names
- `sector` (string, optional): Filter by sector (use values from filters endpoint, or "all")
- `country` (string, optional): Filter by country (use values from filters endpoint, or "all")  
- `status` (string, optional): Filter by status ("all", "pending", "approved", "rejected")
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 10)

## Search Functionality

### Search by Company Information:
- **Company Name**: `?search=Test Company`
- **VAT Number**: `?search=VAT123`
- **Email**: `?search=company@example.com`
- **Country**: `?search=Sweden`

### Search by Associated User Names:
- **First Name**: `?search=Mario`
- **Last Name**: `?search=Rossi`
- **Full Name**: `?search=Mario Rossi`
- **User Email**: `?search=mario@company.com`

## Filter Examples

### Single Filters:
```
GET /api/company/admin/companies/?sector=construction
GET /api/company/admin/companies/?country=Sweden
GET /api/company/admin/companies/?status=pending
```

### Combined Filters:
```
GET /api/company/admin/companies/?search=Test&sector=manufacturing%20%20%26%20Production&status=approved
GET /api/company/admin/companies/?search=Mario&country=Sweden
```

### Pagination:
```
GET /api/company/admin/companies/?page=2&page_size=20
```

## Response Format

```json
{
  "count": 25,
  "next": true,
  "previous": false,
  "results": [
    {
      "id": 1,
      "companyName": "Example Company",
      "vatNumber": "VAT123456",
      "country": "Sweden",
      "sector": "manufacturing  & Production",
      "companyEmail": "company@example.com",
      "status": "approved",
      "registrationDate": "2025-07-28",
      "contacts": [
        {
          "name": "John Doe",
          "email": "john@example.com",
          "position": "Manager"
        }
      ]
    }
  ],
  "page_size": 10,
  "total_pages": 3,
  "current_page": 1
}
```

## Frontend Implementation Notes

1. **Load Filter Options**: Call `/api/company/filters/` on page load to populate dropdown menus
2. **Search Implementation**: Use debounced search input to avoid excessive API calls
3. **URL State Management**: Consider updating URL parameters to maintain filter state on page refresh
4. **Loading States**: Show loading indicators during API calls
5. **Error Handling**: Handle API errors gracefully with user-friendly messages

## Performance Considerations

- Search queries are optimized with database indexing
- Results are paginated to improve performance
- Use `distinct()` to avoid duplicate results when searching across related models
- Prefetch related user data to minimize database queries
