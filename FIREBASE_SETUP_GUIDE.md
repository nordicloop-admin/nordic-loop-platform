# 🔥 Firebase Storage Setup Guide - Django Backend

## Overview

This guide will help you set up Firebase Storage for handling image uploads in your Nordic Loop platform. Firebase Storage provides secure, scalable, and reliable cloud storage for user-uploaded images.

## 🚀 **Step 1: Create Firebase Project**

### 1.1 Go to Firebase Console
- Visit [Firebase Console](https://console.firebase.google.com/)
- Sign in with your Google account

### 1.2 Create New Project
```bash
1. Click "Create a project"
2. Enter project name: "nordic-loop-platform" (or your preferred name)
3. Choose whether to enable Google Analytics (optional)
4. Click "Create project"
```

### 1.3 Enable Firebase Storage
```bash
1. In Firebase Console, go to "Build" → "Storage"
2. Click "Get started"
3. Choose "Start in test mode" (we'll configure security rules later)
4. Select your storage location (choose closest to your users)
5. Click "Done"
```

## 🔧 **Step 2: Configure Authentication & Service Account**

### 2.1 Create Service Account
```bash
1. Go to Project Settings (gear icon) → "Service accounts"
2. Click "Generate new private key"
3. Download the JSON file
4. Rename it to "firebase-credentials.json"
5. Store it securely (DO NOT commit to version control)
```

### 2.2 Set Environment Variables

#### **For Development (.env file):**
```bash
# Add to your .env file
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

#### **For Production (Render.com):**
```bash
# Environment Variables to set on Render:
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com

# Option 1: Upload service account JSON content
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}

# Option 2: Set individual Firebase config variables
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nXXXXX\n-----END PRIVATE KEY-----
```

## 🔒 **Step 3: Configure Firebase Security Rules**

### 3.1 Update Storage Rules
In Firebase Console → Storage → Rules, replace with:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow read access to all files
    match /{allPaths=**} {
      allow read: if true;
    }
    
    // Allow write access only to authenticated users for their own files
    match /material_images/user_{userId}/{allPaths=**} {
      allow write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Allow admin/backend service to write anywhere
    match /{allPaths=**} {
      allow write: if request.auth != null && 
        request.auth.token.admin == true;
    }
  }
}
```

### 3.2 Alternative Simple Rules (for testing)
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read, write: if true;
    }
  }
}
```

## ⚙️ **Step 4: Update Django Settings**

### 4.1 Install Dependencies
```bash
pip install firebase-admin
pip freeze > requirements.txt
```

### 4.2 Django Settings Configuration
The settings are already configured in `core/settings.py`:

```python
# Firebase Configuration
FIREBASE_STORAGE_BUCKET = env('FIREBASE_STORAGE_BUCKET', default='your-project-id.appspot.com')
FIREBASE_CREDENTIALS_PATH = env('FIREBASE_CREDENTIALS_PATH', default=None)
```

## 🗄️ **Step 5: Run Database Migration**

```bash
# Apply the migration to update the model field
python manage.py migrate ads
```

## 🧪 **Step 6: Test Firebase Integration**

### 6.1 Test Upload Functionality
```python
# Run in Django shell
python manage.py shell

from base.services.firebase_service import firebase_storage_service
from django.core.files.uploadedfile import SimpleUploadedFile

# Test basic connectivity
stats = firebase_storage_service.get_storage_stats()
print("Firebase connected successfully:", stats)

# Test image upload (if you have a test image)
with open('path/to/test/image.jpg', 'rb') as f:
    test_file = SimpleUploadedFile(
        name='test.jpg',
        content=f.read(),
        content_type='image/jpeg'
    )
    success, message, url = firebase_storage_service.upload_image(test_file)
    print(f"Upload success: {success}")
    print(f"Message: {message}")
    print(f"URL: {url}")
```

### 6.2 Test API Endpoint
```bash
# Test Step 8 API with image upload
curl -X PUT http://localhost:8000/api/ads/1/step/8/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Test Firebase Upload" \
  -F "description=Testing Firebase Storage integration with a detailed description that meets the minimum requirements" \
  -F "keywords=firebase,test,upload" \
  -F "material_image=@path/to/test/image.jpg"
```

## 🔄 **Step 7: Migration from Local Storage (Optional)**

If you have existing images in local storage, create a migration script:

### 7.1 Create Migration Script
```python
# migration_to_firebase.py
import os
from django.core.management.base import BaseCommand
from ads.models import Ad
from base.services.firebase_service import firebase_storage_service
from django.conf import settings

class Command(BaseCommand):
    help = 'Migrate existing local images to Firebase Storage'
    
    def handle(self, *args, **options):
        ads_with_images = Ad.objects.exclude(material_image__isnull=True).exclude(material_image='')
        
        for ad in ads_with_images:
            if ad.material_image and not ad.material_image.startswith('http'):
                # This is a local file path
                local_path = os.path.join(settings.MEDIA_ROOT, str(ad.material_image))
                
                if os.path.exists(local_path):
                    try:
                        with open(local_path, 'rb') as f:
                            success, message, firebase_url = firebase_storage_service.upload_image(
                                f, 
                                folder='material_images',
                                user_id=ad.user.id if ad.user else None
                            )
                            
                        if success:
                            ad.material_image = firebase_url
                            ad.save()
                            self.stdout.write(f"Migrated {ad.id}: {firebase_url}")
                        else:
                            self.stdout.write(f"Failed to migrate {ad.id}: {message}")
                            
                    except Exception as e:
                        self.stdout.write(f"Error migrating {ad.id}: {str(e)}")
```

### 7.2 Run Migration
```bash
python manage.py migrate_to_firebase
```

## 🔍 **Step 8: Verify Integration**

### 8.1 Check Firebase Console
- Go to Firebase Console → Storage
- You should see uploaded images in the `material_images/` folder
- Images should be publicly accessible

### 8.2 Test Image URLs
- Copy an image URL from Firebase
- Open it in browser - should display the image
- URLs should look like: `https://firebasestorage.googleapis.com/v0/b/your-bucket/o/material_images%2Fuser_1%2Fimage.jpg?alt=media`

### 8.3 Test API Response
When you upload an image via Step 8 API, you should get:
```json
{
  "message": "Material ad completed successfully! Your material is now listed for auction.",
  "step": 8,
  "data": {
    "id": 123,
    "title": "Test Firebase Upload",
    "description": "Testing Firebase Storage integration...",
    "keywords": "firebase,test,upload",
    "material_image": "https://firebasestorage.googleapis.com/v0/b/your-bucket/o/material_images%2Fuser_1%2Ftest_image.jpg?alt=media",
    "current_step": 8,
    "is_complete": true
  }
}
```

## 🚨 **Troubleshooting**

### Common Issues:

#### **1. "Firebase Admin SDK not initialized"**
```bash
Solution: Check FIREBASE_STORAGE_BUCKET and credentials configuration
- Verify .env file has correct values
- Ensure service account JSON is valid
- Check file path for FIREBASE_CREDENTIALS_PATH
```

#### **2. "Permission denied"**
```bash
Solution: Update Firebase Storage rules
- Check Firebase Console → Storage → Rules
- Ensure read access is allowed
- Verify service account has proper permissions
```

#### **3. "Module not found: firebase_admin"**
```bash
Solution: Install dependencies
pip install firebase-admin
```

#### **4. "Invalid storage bucket"**
```bash
Solution: Check bucket name format
- Should be: your-project-id.appspot.com
- Verify in Firebase Console → Storage
```

#### **5. "CORS errors in frontend"**
```bash
Solution: Configure CORS in Firebase
- Go to Firebase Console → Storage
- Configure CORS settings if needed
```

## 📱 **Frontend Integration**

The frontend integration remains the same! Your existing frontend code will work without changes because:

1. **Same API endpoints** - `/api/ads/{id}/step/8/` works identically
2. **Same request format** - FormData with `material_image` field
3. **Same response format** - Returns image URL in `material_image` field
4. **Automatic handling** - Firebase upload happens transparently in backend

### Example Frontend Code (Still Works):
```javascript
const formData = new FormData();
formData.append('title', 'My Ad Title');
formData.append('description', 'Detailed description...');
formData.append('keywords', 'plastic,recycling');
formData.append('material_image', selectedFile); // File object

const response = await fetch(`/api/ads/${adId}/step/8/`, {
    method: 'PUT',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    },
    body: formData
});

const result = await response.json();
console.log('Image URL:', result.data.material_image); // Now a Firebase URL!
```

## 🎯 **Benefits Achieved**

✅ **Scalable Storage** - Unlimited image storage with Firebase  
✅ **Fast CDN Delivery** - Global CDN for fast image loading  
✅ **Secure** - Service account authentication  
✅ **Cost Effective** - Pay only for what you use  
✅ **Reliable** - 99.95% uptime SLA  
✅ **No Server Load** - Images don't consume your server resources  
✅ **Easy Management** - Firebase Console for monitoring  

## 🔐 **Security Best Practices**

1. **Never commit service account JSON** to version control
2. **Use environment variables** for all Firebase config
3. **Implement proper Storage rules** for production
4. **Monitor usage** in Firebase Console
5. **Set up billing alerts** to avoid unexpected costs
6. **Rotate service account keys** periodically

## 📊 **Monitoring & Analytics**

### Firebase Console Metrics:
- **Storage usage** and costs
- **Number of operations** (uploads, downloads)
- **Bandwidth usage**
- **Error rates** and logs

### Django Logging:
Monitor Firebase operations in your Django logs:
```python
# Check logs for Firebase operations
tail -f django.log | grep -i firebase
```

## Firebase Credentials Configuration

The platform supports multiple methods for Firebase authentication to work seamlessly across development and production environments.

### Development Environment

For local development, use a service account file:

```bash
# .env file
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### Production Environment (Render/Heroku/Cloud Platforms)

For production deployments where you can't store files, use environment variables:

#### Option 1: JSON Content as String (Recommended)
```bash
# Set in your cloud platform's environment variables
GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type": "service_account", "project_id": "your-project", ...}'
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

#### Option 2: Standard Google Cloud Variable
```bash
# If your platform supports file-based credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### How It Works

The Firebase service automatically detects and uses credentials in this priority order:

1. **FIREBASE_CREDENTIALS_PATH** - File path (development)
2. **GOOGLE_APPLICATION_CREDENTIALS_JSON** - JSON string (production)
3. **GOOGLE_APPLICATION_CREDENTIALS** - File path (standard)
4. **Default environment authentication** - For Google Cloud Platform

### Setting Up Production Credentials

#### Step 1: Get Your Service Account JSON
1. Go to Firebase Console → Project Settings → Service Accounts
2. Generate new private key → Download JSON file
3. Copy the entire JSON content

#### Step 2: Configure Production Environment

**For Render:**
```bash
# In Render Dashboard → Environment Variables
GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project-id","private_key_id":"abc123...","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE...","client_email":"firebase-adminsdk-...@your-project.iam.gserviceaccount.com","client_id":"123...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-...%40your-project.iam.gserviceaccount.com"}'

FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

**For Heroku:**
```bash
heroku config:set GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
heroku config:set FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

#### Step 3: Test Configuration

Run the migration script to verify credentials:

```bash
# Check status only
python migrate_production_to_firebase.py --status-only

# Should show:
# 🔑 Firebase Credentials:
#    GOOGLE_APPLICATION_CREDENTIALS_JSON: ✅ Set (length: 2456 chars)
#    🔥 Firebase Storage Status: Connected
```

### Troubleshooting

#### Common Issues:

1. **"No Firebase credentials found!"**
   - Ensure you've set the correct environment variable for your environment
   - Check that JSON string is properly escaped

2. **"Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON"**
   - Verify JSON is valid and properly escaped
   - Check for missing quotes or special characters

3. **"Permission denied"**
   - Verify service account has Storage Admin role
   - Check Firebase Storage bucket name is correct

#### Testing Credentials:

```python
# Test script
python -c "
from base.services.firebase_service import firebase_storage_service
stats = firebase_storage_service.get_storage_stats()
print('✅ Firebase connected:', stats)
"
```

### Security Best Practices

1. **Never commit credentials to Git**
   - Use `.env` files for development
   - Use environment variables for production

2. **Limit service account permissions**
   - Only grant necessary Firebase Storage permissions
   - Regularly rotate service account keys

3. **Use different service accounts**
   - Separate accounts for development/staging/production
   - Monitor usage and access logs

Your Firebase Storage integration is now complete! 🎉 