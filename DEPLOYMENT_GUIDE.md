# Render Deployment Guide - Nordic Loop Platform

## Issue Fixed: backports.zoneinfo Error

The `backports.zoneinfo` compilation error has been resolved by:

1. ✅ **Removed incompatible dependency**: `backports.zoneinfo` is only needed for Python < 3.9
2. ✅ **Added conditional dependency**: Now only installs for older Python versions
3. ✅ **Updated Django**: Upgraded to Django 5.2 for better compatibility
4. ✅ **Added runtime specification**: `runtime.txt` specifies Python 3.11.8
5. ✅ **Fixed database config**: Uncommented production database settings

## Files Modified

### 1. `requirements.txt` - Updated Dependencies
```txt
asgiref==3.8.1
dj-database-url==2.3.0
Django==5.2
django-cors-headers==4.7.0
django-environ==0.12.0
django-extensions==4.0
djangorestframework==3.16.0
djangorestframework-simplejwt==5.5.0
gunicorn==23.0.0
pillow==11.2.1
psycopg2-binary==2.9.10
PyJWT==2.9.0
python-dotenv==1.1.0
sqlparse==0.5.3
typing-extensions==4.13.2
whitenoise==6.9.0

# Only install backports.zoneinfo for Python < 3.9
backports.zoneinfo==0.2.1; python_version<"3.9"
```

### 2. `runtime.txt` - Python Version
```txt
python-3.11.8
```

### 3. `render.yaml` - Render Configuration
```yaml
services:
  - type: web
    name: nordic-loop-platform
    env: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn core.wsgi:application"
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: core.settings
      - key: PYTHON_VERSION
        value: 3.11.8
      - key: WEB_CONCURRENCY
        value: 4
```

## Deployment Steps for Render

### 1. Environment Variables
Set these in your Render dashboard:

```bash
# Required
DJANGO_SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/database
DJANGO_ENV=production
DJANGO_DEBUG=False

# Allowed hosts (add your Render URL)
DJANGO_ALLOWED_HOSTS=yourapp.onrender.com,127.0.0.1,localhost

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS=https://yourapp.onrender.com
```

### 2. Database Setup
Render will automatically provide `DATABASE_URL` if you add a PostgreSQL database.

### 3. Deploy Process
1. **Connect Repository**: Link your GitHub repo to Render
2. **Select Service Type**: Web Service
3. **Build Command**: `./build.sh`
4. **Start Command**: `gunicorn core.wsgi:application`
5. **Environment**: Python
6. **Python Version**: 3.11.8 (specified in runtime.txt)

### 4. Build Script (`build.sh`)
```bash
#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
```

## Troubleshooting

### Common Issues & Solutions

#### 1. backports.zoneinfo Build Error ✅ FIXED
**Error**: `error: command '/usr/bin/gcc' failed with exit code 1`
**Solution**: Conditional dependency in requirements.txt

#### 2. Database Connection Issues
**Error**: `FATAL: password authentication failed`
**Solution**: 
- Check `DATABASE_URL` environment variable
- Ensure PostgreSQL service is running
- Verify database credentials

#### 3. Static Files Not Loading
**Error**: CSS/JS files not found
**Solution**:
- Ensure `whitenoise` is in MIDDLEWARE
- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATIC_URL` settings

#### 4. CORS Errors
**Error**: Cross-origin requests blocked
**Solution**:
- Add your frontend URL to `CORS_ALLOWED_ORIGINS`
- Include your Render URL in allowed origins

#### 5. SSL/HTTPS Issues
**Error**: Mixed content warnings
**Solution**:
- Ensure `SECURE_PROXY_SSL_HEADER` is set
- Add your domain to `CSRF_TRUSTED_ORIGINS`

## Production Checklist

### ✅ Security
- [x] `SECRET_KEY` set via environment variable
- [x] `DEBUG = False` in production
- [x] `ALLOWED_HOSTS` configured
- [x] CSRF protection enabled
- [x] SSL redirect enabled

### ✅ Performance
- [x] `gunicorn` WSGI server
- [x] `whitenoise` for static files
- [x] Database connection pooling
- [x] Proper caching headers

### ✅ Monitoring
- [x] Error logging configured
- [x] Health check endpoint available
- [x] Database connection monitoring

## Sample Data on Production

To create sample data on production:

```bash
# SSH into Render container or use Render Shell
python create_sample_ads_and_bids.py
```

Or create a management command:
```bash
python manage.py shell
# Then run the sample data functions
```

## Testing Deployment

After successful deployment:

1. **Health Check**: `GET https://yourapp.onrender.com/api/ads/`
2. **Authentication**: `POST https://yourapp.onrender.com/api/users/login/`
3. **Admin Panel**: `https://yourapp.onrender.com/admin/`

## Performance Tips

1. **Database**: Use PostgreSQL for production
2. **Static Files**: Whitenoise handles static file serving
3. **Caching**: Consider Redis for session/cache storage
4. **CDN**: Use Cloudflare for better global performance

## Support

If deployment still fails:

1. Check Render build logs for specific errors
2. Verify all environment variables are set
3. Test locally with `DJANGO_ENV=production`
4. Check Django's deployment checklist: `python manage.py check --deploy`

## Updated Dependencies

The requirements.txt now includes all necessary packages for a production Django deployment:

- **Django 5.2**: Latest stable version
- **gunicorn**: Production WSGI server
- **psycopg2-binary**: PostgreSQL adapter
- **whitenoise**: Static file serving
- **django-cors-headers**: CORS handling
- **djangorestframework**: REST API framework
- **django-environ**: Environment variable management

All packages are compatible with Python 3.11+ and Render's deployment environment. 