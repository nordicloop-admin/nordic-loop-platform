# Quick Start: Cloning Data from dbv2.sqlite3

## ✅ Successfully Created Scripts

I've created two database cloning scripts for you:

1. **`clone_dbv2_simple.py`** - ⭐ **Recommended** - Works without Django setup
2. **`clone_dbv2_data.py`** - Full Django-integrated version (requires Django environment)

## 🚀 Quick Usage Examples

### 1. Analyze Database Structure
```bash
python clone_dbv2_simple.py --analyze-only
```
**Output**: Shows all tables, columns, and row counts

### 2. Complete Backup (All Formats)
```bash
python clone_dbv2_simple.py --formats sql json csv copy
```
**Creates**:
- `cloned_data/dbv2_dump_YYYYMMDD_HHMMSS.sql` - Complete SQL dump
- `cloned_data/dbv2_data_YYYYMMDD_HHMMSS.json` - All data as JSON
- `cloned_data/csv_export/[table].csv` - Each table as CSV
- `cloned_data/dbv2_copy_YYYYMMDD_HHMMSS.sqlite3` - Exact copy

### 3. Quick SQL Backup Only
```bash
python clone_dbv2_simple.py --formats sql
```

### 4. Clone to Another Database
```bash
python clone_dbv2_simple.py --formats clone --target backup.sqlite3
```

### 5. Examine Specific Table
```bash
python clone_dbv2_simple.py --table-details ads_ad
```

## 📊 Your Database Analysis Results

From `dbv2.sqlite3`:
- **18 tables** with **409 total records**
- Key tables:
  - `ads_ad`: 27 ads with complete 8-step data
  - `bids_bid`: 41 bids from users
  - `users_user`: 13 user accounts
  - `company_company`: 5 company profiles
  - `category_subcategory`: 155 material subcategories

## 📁 Output Structure

After running the export, you'll have:
```
cloned_data/
├── dbv2_dump_20250610_224132.sql       # Complete SQL dump (69KB)
├── dbv2_data_20250610_224132.json      # All data as JSON (109KB)
├── dbv2_copy_20250610_224132.sqlite3   # Exact database copy (288KB)
└── csv_export/                         # Individual CSV files
    ├── ads_ad.csv                      # 27 ads
    ├── bids_bid.csv                    # 41 bids
    ├── users_user.csv                  # 13 users
    ├── company_company.csv             # 5 companies
    └── ... (14 more table files)
```

## 🔧 Available Options

```bash
python clone_dbv2_simple.py [OPTIONS]

-s, --source PATH      Source database (default: dbv2.sqlite3)
-t, --target PATH      Target database (default: db.sqlite3)
-f, --formats FORMAT   Export formats: sql, json, csv, clone, copy
-a, --analyze-only     Just analyze structure
-d, --table-details    Show details for specific table
-l, --list-tables      List all tables
```

## 🎯 Common Use Cases

### Database Migration
```bash
# Clone to production database
python clone_dbv2_simple.py --formats clone --target production.sqlite3
```

### Create Backup Before Changes
```bash
# Full backup with timestamp
python clone_dbv2_simple.py --formats copy sql
```

### Data Analysis
```bash
# Export to CSV for analysis in Excel/Pandas
python clone_dbv2_simple.py --formats csv
```

### Django Integration
```bash
# For Django development (requires Django environment)
python clone_dbv2_data.py --formats fixtures
python manage.py loaddata cloned_data/dbv2_fixtures_*.json
```

## ⚠️ Important Notes

1. **Backup Safety**: Target database is automatically backed up before cloning
2. **File Locations**: All exports go to `cloned_data/` directory
3. **Timestamps**: All files include timestamps to prevent overwrites
4. **Large Data**: JSON export loads all data into memory (409 records = small, no issues)

## 🔥 Quick Commands for Your Workflow

```bash
# Complete backup right now
python clone_dbv2_simple.py --formats sql json copy

# Check what's in the database
python clone_dbv2_simple.py --analyze-only

# See sample ads data
python clone_dbv2_simple.py --table-details ads_ad

# Clone to your main database
python clone_dbv2_simple.py --formats clone --target db.sqlite3
```

## ✨ Success!

Your data cloning scripts are ready to use. The simplified version (`clone_dbv2_simple.py`) works immediately without any configuration. The data from `dbv2.sqlite3` includes:

- **Complete Nordic Loop platform data**
- **Real auction data** with 27 ads
- **User accounts and companies**
- **Bidding history and transactions**
- **Full category and subcategory structure**

You can now safely clone, backup, analyze, or migrate this data as needed! 