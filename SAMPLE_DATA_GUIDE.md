# Sample Data Guide - Nordic Loop Platform

## Overview

This guide explains the comprehensive sample data created for testing and demonstration of the Nordic Loop marketplace platform. The sample data includes realistic material ads, users, companies, locations, and active bids.

## Scripts Available

### 1. `create_sample_ads_and_bids.py`
Creates comprehensive sample data including:
- Additional users and companies
- Complete material ads with 8-step data
- Realistic bids from different users
- Multiple locations across Nordic countries

### 2. `reset_sample_data.py`
Utility script to clean up sample data:
- **Normal reset**: Removes sample data, keeps original test users
- **Complete reset**: `--all` flag removes ALL data except superusers

### 3. `setup_test_data.py`
Original script that creates:
- Basic categories and subcategories
- Test users and companies
- Admin user

## Sample Data Created

### 🧑‍💼 Users & Companies

| User | Email | Company | Country |
|------|-------|---------|---------|
| Maria Andersson | maria@ecorecycle.se | EcoRecycle Solutions AB | Sweden |
| Erik Lundberg | erik@plasticorp.com | PlastiCorp Industries | Sweden |
| Anna Pettersson | anna@greenmaterials.eu | Green Materials Ltd | Sweden |
| John Doe | test@nordicloop.com | Test Nordic Company AB | Sweden |
| Admin User | admin@nordicloop.com | Test Nordic Company AB | Sweden |

**Password for all users**: `testpass123`

### 📍 Locations

1. **Stockholm, Sweden** - Industrivägen 15, 11234
2. **Gothenburg, Sweden** - Hamngatan 42, 41108  
3. **Malmö, Sweden** - Österport 88, 21120
4. **Oslo, Norway** - Nydalen Park 25, 0484
5. **Copenhagen, Denmark** - Ørestads Boulevard 73, 2300

### 🏭 Material Ads/Auctions

#### 1. Premium PP Pellets - Automotive Grade
- **Category**: Plastics > PP
- **Location**: Stockholm, Sweden
- **Quantity**: 150 tons
- **Starting Price**: €1,250/ton
- **Reserve Price**: €1,400/ton
- **Origin**: Post-industrial
- **Contamination**: Clean
- **Processing**: Extrusion, Injection Moulding

#### 2. Clean HDPE Milk Bottles - Weekly Supply
- **Category**: Plastics > HDPE
- **Location**: Gothenburg, Sweden
- **Quantity**: 75 tons
- **Starting Price**: €850/ton
- **Reserve Price**: €950/ton
- **Origin**: Post-consumer
- **Contamination**: Slightly contaminated
- **Processing**: Blow Moulding, Extrusion

#### 3. Clear PET Bottles - Beverage Grade Quality
- **Category**: Plastics > PET
- **Location**: Malmö, Sweden
- **Quantity**: 200 tons
- **Starting Price**: €950/ton
- **Reserve Price**: €1,100/ton
- **Origin**: Post-consumer
- **Contamination**: Clean
- **Processing**: Blow Moulding, Thermoforming

#### 4. Industrial Corrugated Cardboard - Weekly Supply
- **Category**: Paper > Cardboard
- **Location**: Oslo, Norway
- **Quantity**: 300 tons
- **Starting Price**: €180/ton
- **Reserve Price**: €220/ton
- **Origin**: Post-industrial
- **Contamination**: Clean
- **Processing**: Calendering

#### 5. Sorted Aluminum Cans - Premium Quality
- **Category**: Metals > Aluminum
- **Location**: Copenhagen, Denmark
- **Quantity**: 50 tons
- **Starting Price**: €1,800/ton
- **Reserve Price**: €2,000/ton
- **Origin**: Post-consumer
- **Contamination**: Clean
- **Processing**: Sintering

### 💰 Active Bids

Each material has **2-5 active bids** from different users with increasing bid amounts. Bid amounts typically range from 5-15% above the previous bid, creating realistic auction competition.

**Example bidding activity**:
- PP Pellets: 4 bids, highest €1,623.62
- HDPE Bottles: 4 bids, highest €1,208.32
- PET Bottles: 3 bids, highest €1,319.54
- Cardboard: 4 bids, highest €273.91
- Aluminum Cans: 2 bids, highest €2,071.15

## Running the Scripts

### Create Sample Data
```bash
python create_sample_ads_and_bids.py
```

### Reset Sample Data (keeps test users)
```bash
python reset_sample_data.py
```

### Complete Reset (removes everything except superusers)
```bash
python reset_sample_data.py --all
```

### Create Basic Test Data (categories, test users)
```bash
python setup_test_data.py
```

## API Testing with Sample Data

### 1. Authentication
```bash
# Login as any user
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "maria@ecorecycle.se", "password": "testpass123"}'
```

### 2. List All Materials
```bash
curl -X GET "http://localhost:8000/api/ads/"
```

### 3. Filter by Category
```bash
curl -X GET "http://localhost:8000/api/ads/?category=1"  # Plastics
curl -X GET "http://localhost:8000/api/ads/?category=2"  # Paper
curl -X GET "http://localhost:8000/api/ads/?category=3"  # Metals
```

### 4. Filter by Location
```bash
curl -X GET "http://localhost:8000/api/ads/?country=Sweden"
curl -X GET "http://localhost:8000/api/ads/?city=Stockholm"
```

### 5. Filter by Origin
```bash
curl -X GET "http://localhost:8000/api/ads/?origin=post_industrial"
curl -X GET "http://localhost:8000/api/ads/?origin=post_consumer"
```

### 6. Get User's Materials (requires authentication)
```bash
curl -X GET "http://localhost:8000/api/ads/user/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 7. List Bids (requires authentication)
```bash
curl -X GET "http://localhost:8000/api/bids/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8. Get Specific Material Details
```bash
curl -X GET "http://localhost:8000/api/ads/1/"
```

## Database Stats After Sample Data Creation

- **👥 Total Users**: 5
- **🏢 Total Companies**: 4  
- **📍 Total Locations**: 5
- **🏭 Total Ads**: 10-15 (varies by run)
- **💰 Total Bids**: 15-25 (varies by run)
- **📂 Categories**: 5 main categories
- **📋 Subcategories**: ~15 subcategories

## Use Cases for Sample Data

### 1. **Frontend Development**
- Test material listings with real data
- Implement search and filtering
- Build bidding interfaces
- Test responsive design with various content lengths

### 2. **API Testing**
- Comprehensive endpoint testing
- Authentication workflow testing
- Data validation testing
- Performance testing with realistic data volumes

### 3. **Demo & Presentation**
- Show realistic marketplace scenarios
- Demonstrate bidding functionality
- Present different material types and locations
- Showcase Nordic market diversity

### 4. **Load Testing**
- Test with multiple concurrent users
- Simulate realistic auction scenarios
- Test database performance with relationships
- Benchmark API response times

## Data Relationships

```
Users ──┐
        ├─── Companies
        └─── Ads ──┐
                   ├─── Categories/Subcategories
                   ├─── Locations
                   └─── Bids ──── Users (bidders)
```

## Material Specifications Examples

Each material includes realistic specifications:
- **PP Pellets**: Melt Flow Index, Density, FDA approval
- **HDPE Bottles**: Density, cleanliness, sorting info
- **PET Bottles**: Clarity, sizes, label status
- **Cardboard**: Brown corrugated, dry storage conditions
- **Aluminum**: Magnetic sorting, compression details

## Geographic Distribution

Materials are distributed across Nordic countries:
- **Sweden**: 3 locations (Stockholm, Gothenburg, Malmö)
- **Norway**: 1 location (Oslo)
- **Denmark**: 1 location (Copenhagen)

This creates realistic cross-border trading scenarios and logistics considerations.

## Pricing Diversity

Starting prices range from:
- **Low**: €180/ton (Cardboard)
- **Medium**: €850-950/ton (Plastics)
- **High**: €1,800/ton (Aluminum)

This demonstrates the platform's ability to handle various material value ranges.

## Tips for Development

1. **Always reset data** before important demos
2. **Use different user logins** to test permissions
3. **Check bid sequences** to ensure logical progression
4. **Test filtering combinations** with the diverse data set
5. **Monitor auction end dates** - some may expire during testing

## Troubleshooting

### Issue: No bids showing
- Check authentication - bids endpoint requires login
- Verify user permissions
- Check if bids were created successfully

### Issue: Duplicate data
- Run `reset_sample_data.py` before recreating
- Check for existing users/companies before running script

### Issue: Foreign key errors
- Ensure basic categories exist (run `setup_test_data.py` first)
- Check that users and companies are properly linked

## Next Steps

1. **Extend sample data** with more materials
2. **Add auction end scenarios** (expired auctions)
3. **Create winning bid scenarios** 
4. **Add international locations** beyond Nordic countries
 