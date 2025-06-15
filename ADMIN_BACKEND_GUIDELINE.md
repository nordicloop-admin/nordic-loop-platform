# Backend API Guideline for Admin Dashboard

This document outlines the required backend endpoints, request/response structures, and data models for supporting the admin dashboard of the Nordic Loop Marketplace. The goal is to ensure seamless integration between the frontend admin UI and the backend services.

---

## 1. Companies Management

### Endpoints

- `GET /admin/companies`
  - **Query Params:** `search`, `status` (`all`, `pending`, `approved`, `rejected`)
  - **Response:**
    ```json
    [
      {
        "id": "1",
        "companyName": "Eco Solutions AB",
        "vatNumber": "SE123456789001",
        "country": "Sweden",
        "sector": "Recycling & Waste Management",
        "companyEmail": "info@ecosolutions.se",
        "companyPhone": "+46 8 123 45 67",
        "contacts": [
          {
            "name": "Erik Johansson",
            "email": "erik@ecosolutions.se",
            "position": "Sustainability Manager"
          }
        ],
        "status": "approved",
        "createdAt": "2023-05-15"
      }
    ]
    ```

- `POST /admin/companies`
  - **Request:**
    ```json
    {
      "companyName": "string",
      "vatNumber": "string",
      "country": "string",
      "sector": "string",
      "companyEmail": "string",
      "companyPhone": "string",
      "contacts": [
        {
          "name": "string",
          "email": "string",
          "position": "string"
        }
      ]
    }
    ```
  - **Response:** Created company object

- `PATCH /admin/companies/{id}/status`
  - **Request:** `{ "status": "approved" | "pending" | "rejected" }`
  - **Response:** Updated company object

- `GET /admin/companies/{id}`
  - **Response:** Company object (see above)

- `PUT /admin/companies/{id}`
  - **Request:** Same as POST
  - **Response:** Updated company object

- `DELETE /admin/companies/{id}`
  - **Response:** Success/failure

---

## 2. Users Management

### Endpoints

- `GET /admin/users`
  - **Query Params:** `search`
  - **Response:**
    ```json
    [
      {
        "id": "1",
        "email": "erik@ecosolutions.se",
        "firstName": "Erik",
        "lastName": "Johansson",
        "position": "Sustainability Manager",
        "companyId": "1",
        "companyName": "Eco Solutions AB",
        "createdAt": "2023-05-15"
      }
    ]
    ```

- `POST /admin/users`
  - **Request:**
    ```json
    {
      "email": "string",
      "firstName": "string",
      "lastName": "string",
      "position": "string",
      "companyId": "string"
    }
    ```
  - **Response:** Created user object

- `GET /admin/users/{id}`
  - **Response:** User object

- `PUT /admin/users/{id}`
  - **Request:** Same as POST
  - **Response:** Updated user object

- `PATCH /admin/users/{id}/status`
  - **Request:** `{ "active": true | false }`
  - **Response:** Updated user object

- `DELETE /admin/users/{id}`
  - **Response:** Success/failure

---

## 3. Bids Management

### Endpoints

- `GET /admin/bids`
  - **Query Params:** `search`, `status` (`all`, `active`, `pending`, `outbid`, `rejected`)
  - **Response:**
    ```json
    [
      {
        "id": "1",
        "itemId": "1",
        "itemName": "PPA Thermocomp UFW49RSC (Black)",
        "bidAmount": "5,250,000",
        "previousBid": "5,150,000",
        "bidderName": "Erik Johansson",
        "bidderCompany": "Eco Solutions AB",
        "bidderEmail": "erik@ecosolutions.se",
        "status": "active",
        "isHighest": true,
        "createdAt": "2023-05-15 14:30",
        "expiresAt": "2023-05-18 14:30",
        "needsReview": false
      }
    ]
    ```

- `PATCH /admin/bids/{id}/status`
  - **Request:** `{ "status": "active" | "rejected" }`
  - **Response:** Updated bid object

---

## 4. Marketplace Listings Management

### Endpoints

- `GET /admin/marketplace`
  - **Query Params:** `search`, `status` (`all`, `active`, `pending`, `inactive`)
  - **Response:**
    ```json
    [
      {
        "id": "1",
        "name": "PPA Thermocomp UFW49RSC (Black)",
        "category": "Plastics",
        "basePrice": "5,013,008",
        "highestBid": "5,250,000",
        "status": "active",
        "volume": "500 kg",
        "seller": "Eco Solutions AB",
        "countryOfOrigin": "Sweden",
        "createdAt": "2023-05-15",
        "image": "/images/marketplace/categories/plastics.jpg"
      }
    ]
    ```

- `POST /admin/marketplace`
  - **Request:**
    ```json
    {
      "name": "string",
      "category": "string",
      "basePrice": "string",
      "volume": "string",
      "seller": "string",
      "countryOfOrigin": "string",
      "image": "string"
    }
    ```
  - **Response:** Created listing object

- `PATCH /admin/marketplace/{id}/status`
  - **Request:** `{ "status": "active" | "pending" | "inactive" }`
  - **Response:** Updated listing object

- `GET /admin/marketplace/{id}`
  - **Response:** Listing object

- `PUT /admin/marketplace/{id}`
  - **Request:** Same as POST
  - **Response:** Updated listing object

- `DELETE /admin/marketplace/{id}`
  - **Response:** Success/failure

---

## 5. Subscriptions Management

### Endpoints

- `GET /admin/subscriptions`
  - **Query Params:** `search`, `plan`, `status`
  - **Response:**
    ```json
    [
      {
        "id": "1",
        "companyId": "1",
        "companyName": "Eco Solutions AB",
        "plan": "premium",
        "status": "active",
        "startDate": "2023-01-15",
        "endDate": "2024-01-15",
        "autoRenew": true,
        "paymentMethod": "credit_card",
        "lastPayment": "2023-01-15",
        "amount": "799 SEK",
        "contactName": "Erik Johansson",
        "contactEmail": "erik@ecosolutions.se"
      }
    ]
    ```

- `PATCH /admin/subscriptions/{id}/status`
  - **Request:** `{ "status": "active" | "expired" | "payment_failed" }`
  - **Response:** Updated subscription object

---

## 6. Addresses Management

### Endpoints

- `GET /admin/addresses`
  - **Query Params:** `search`, `type`, `verified`
  - **Response:**
    ```json
    [
      {
        "id": "1",
        "companyId": "1",
        "companyName": "Eco Solutions AB",
        "type": "business",
        "addressLine1": "Storgatan 45",
        "addressLine2": "",
        "city": "Stockholm",
        "postalCode": "11455",
        "country": "Sweden",
        "isVerified": true,
        "isPrimary": true,
        "contactName": "Erik Johansson",
        "contactPhone": "+46 70 123 4567",
        "createdAt": "2023-05-15"
      }
    ]
    ```

- `PATCH /admin/addresses/{id}/verify`
  - **Request:** `{ "isVerified": true | false }`
  - **Response:** Updated address object

---

## General Notes

- All endpoints should be protected with admin authentication and authorization.
- Use pagination for list endpoints where data can be large.
- Support filtering and searching as described.
- Use standard HTTP status codes for success and error responses.
- All date/time fields should be in ISO 8601 format.
- All IDs should be UUIDs or unique strings.

---

This guideline should be used as a reference for backend developers to implement the required endpoints and data models to support the admin dashboard UI. If you need more details for a specific section or want to expand on error handling, validation, or authentication, let me know! 