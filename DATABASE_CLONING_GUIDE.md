# Database Cloning Guide

This guide explains how to use the `clone_dbv2_data.py` script to clone all data from `dbv2.sqlite3`.

## Features

The script provides multiple export options:

- **SQL Dump**: Complete database dump as SQL file
- **JSON Export**: All data exported as structured JSON
- **CSV Export**: Each table exported as separate CSV files
- **Django Fixtures**: Django-compatible fixture files
- **Direct Clone**: Clone data directly to another SQLite database

## Usage

### Basic Usage

```bash
# Clone with all default export formats (SQL, JSON, CSV, Fixtures)
python clone_dbv2_data.py

# Analyze database structure only
python clone_dbv2_data.py --analyze-only

# Export only specific formats
python clone_dbv2_data.py --formats sql json

# Clone to a different target database
python clone_dbv2_data.py --target my_backup.sqlite3 --formats clone
```

### Command Line Options

```bash
python clone_dbv2_data.py [OPTIONS]

Options:
  -s, --source PATH      Source database path (default: dbv2.sqlite3)
  -t, --target PATH      Target database path (default: db.sqlite3)
  -f, --formats FORMAT   Export formats: sql, json, csv, fixtures, clone
  -a, --analyze-only     Only analyze database structure, no exports
  -h, --help            Show help message
```

### Export Formats

#### 1. SQL Dump (`sql`)
Creates a complete SQL dump file that can be imported into any SQLite database:
```bash
python clone_dbv2_data.py --formats sql
```
Output: `cloned_data/dbv2_dump_YYYYMMDD_HHMMSS.sql`

#### 2. JSON Export (`json`)
Exports all data as structured JSON:
```bash
python clone_dbv2_data.py --formats json
```
Output: `cloned_data/dbv2_data_YYYYMMDD_HHMMSS.json`

#### 3. CSV Export (`csv`)
Exports each table as a separate CSV file:
```bash
python clone_dbv2_data.py --formats csv
```
Output: `cloned_data/csv_export/[table_name].csv`

#### 4. Django Fixtures (`fixtures`)
Creates Django-compatible fixture files:
```bash
python clone_dbv2_data.py --formats fixtures
```
Output: `cloned_data/dbv2_fixtures_YYYYMMDD_HHMMSS.json`

To load fixtures into Django:
```bash
python manage.py loaddata cloned_data/dbv2_fixtures_YYYYMMDD_HHMMSS.json
```

#### 5. Direct Clone (`clone`)
Clones data directly to another SQLite database:
```bash
python clone_dbv2_data.py --formats clone --target backup.sqlite3
```

## Example Workflows

### Complete Backup
```bash
# Create all export formats for comprehensive backup
python clone_dbv2_data.py
```

### Quick Analysis
```bash
# Check database structure and content
python clone_dbv2_data.py --analyze-only
```

### Import to Django
```bash
# Create Django fixtures and load them
python clone_dbv2_data.py --formats fixtures
python manage.py loaddata cloned_data/dbv2_fixtures_*.json
```

### Database Migration
```bash
# Clone to production database
python clone_dbv2_data.py --formats clone --target production.sqlite3
```

## Output Structure

All exports are saved to the `cloned_data/` directory:

```
cloned_data/
├── dbv2_dump_20241223_143052.sql       # SQL dump
├── dbv2_data_20241223_143052.json      # JSON export
├── dbv2_fixtures_20241223_143052.json  # Django fixtures
└── csv_export/                         # CSV files
    ├── users_user.csv
    ├── company_company.csv
    ├── ads_ad.csv
    └── ...
```

## Safety Features

- **Automatic Backups**: When cloning to existing database, creates backup
- **Error Handling**: Comprehensive error handling and rollback
- **Data Validation**: Validates source database before processing
- **Timestamped Files**: All outputs include timestamps to prevent overwrites

## Troubleshooting

### Common Issues

1. **File Not Found**: Ensure `dbv2.sqlite3` exists in current directory
2. **Permission Errors**: Check file permissions and disk space
3. **Django Import Errors**: Ensure Django environment is properly setup

### Error Messages

- `Source database dbv2.sqlite3 not found`: Check file path
- `Error cloning database`: Database might be locked or corrupted
- `No Django model mappings found`: Source database doesn't match Django models

## Advanced Usage

### Custom Source Path
```bash
python clone_dbv2_data.py --source /path/to/custom.sqlite3
```

### Multiple Operations
```bash
# First analyze, then export specific formats
python clone_dbv2_data.py --analyze-only
python clone_dbv2_data.py --formats sql json
```

### Batch Processing
```bash
# Process multiple databases
for db in *.sqlite3; do
    python clone_dbv2_data.py --source "$db" --formats sql
done
```

## Integration with Django

The script is designed to work seamlessly with Django:

1. **Model Mapping**: Automatically maps common Django table names
2. **Fixtures Support**: Creates Django-compatible fixture files
3. **Settings Integration**: Uses Django settings for database configuration

## Performance Considerations

- Large databases may take significant time to export
- CSV export creates multiple files, which may be slower for many tables
- Direct cloning is fastest for SQLite-to-SQLite transfers
- JSON export uses more memory for large datasets

## Security Notes

- **Backup First**: Always backup target database before cloning
- **Data Sensitivity**: Be cautious with exported files containing sensitive data
- **File Permissions**: Exported files inherit current user permissions
- **Clean Up**: Remove temporary export files after use if they contain sensitive data 