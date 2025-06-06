# 📋 Step 8 Validation Guide - Title, Description & Image Upload

This guide provides detailed validation requirements for Step 8 of the Nordic Loop ad creation system.

## 🎯 Step 8: Final Step - Complete Your Ad

**Endpoint:** `PUT /api/ads/{ad_id}/step/8/`

**Content-Type:** `multipart/form-data` (when uploading image) OR `application/json` (without image)

## 🔍 **Required Fields & Validation Rules**

### **1. `title` (String - REQUIRED)**
```javascript
// Validation Rules:
- REQUIRED: Cannot be null, empty, or only whitespace
- MINIMUM LENGTH: 10 characters (after trimming whitespace)
- MAXIMUM LENGTH: 255 characters (Django model limit)
- AUTOMATIC TRIMMING: Leading/trailing spaces removed

// ✅ Valid Examples:
"Premium HDPE Material - High Quality"           // 37 chars - ✅ Valid
"High-Quality PP Industrial Pellets - Food Grade" // 45 chars - ✅ Valid
"Recycled PET Bottles for Manufacturing"         // 39 chars - ✅ Valid

// ❌ Invalid Examples:
""                          // Empty string - ❌ Invalid
"Short"                     // 5 chars - ❌ Too short
"   Brief   "              // 5 chars after trim - ❌ Too short
null                        // Null value - ❌ Invalid
```

### **2. `description` (Text - REQUIRED)**
```javascript
// Validation Rules:
- REQUIRED: Cannot be null, empty, or only whitespace
- MINIMUM LENGTH: 50 characters (after trimming whitespace)
- NO MAXIMUM LENGTH: TextField in Django (unlimited)
- AUTOMATIC TRIMMING: Leading/trailing spaces removed

// ✅ Valid Example:
"High-quality HDPE material perfect for manufacturing applications. Clean, sorted, and ready for processing. This material comes from post-industrial waste and has been thoroughly cleaned and prepared."

// ❌ Invalid Examples:
""                                    // Empty - ❌ Invalid
"Too short description here"          // 27 chars - ❌ Too short
"   Short after trimming   "         // Under 50 chars after trim - ❌ Invalid
null                                  // Null value - ❌ Invalid
```

### **3. `keywords` (String - OPTIONAL)**
```javascript
// Validation Rules:
- OPTIONAL: Can be null, empty, or omitted
- MAXIMUM LENGTH: 500 characters (Django model limit)
- NO MINIMUM LENGTH: Any length acceptable
- SUGGESTED FORMAT: Comma-separated keywords

// ✅ Valid Examples:
"HDPE, plastic, recycling, manufacturing, food grade"
"PP, polypropylene, industrial, pellets"
""                                    // Empty - ✅ Valid (optional)
null                                  // Null - ✅ Valid (optional)

// ❌ Invalid Examples:
// (Over 500 characters would be invalid)
```

### **4. `material_image` (File - OPTIONAL)**
```javascript
// Validation Rules:
- OPTIONAL: Can be omitted
- FILE TYPE: Image files only (JPEG, PNG, GIF, etc.)
- DJANGO SETTING: Uses ImageField validation
- UPLOAD PATH: Stored in 'material_images/' directory
- NO SIZE LIMIT: Unless configured in Django settings

// ✅ Valid Examples:
- JPEG image file (.jpg, .jpeg)
- PNG image file (.png)
- GIF image file (.gif)
- BMP image file (.bmp)
- WebP image file (.webp)

// ❌ Invalid Examples:
- PDF files (.pdf)
- Word documents (.doc, .docx)
- Text files (.txt)
- Non-image files
```

## 📤 **Request Format Options**

### **Option 1: JSON Request (No Image)**
```javascript
// Headers:
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN

// Request Body:
{
  "title": "Premium HDPE Material - High Quality",
  "description": "High-quality HDPE material perfect for manufacturing applications. Clean, sorted, and ready for processing. This material comes from post-industrial waste and has been thoroughly cleaned and prepared for use in various manufacturing processes.",
  "keywords": "HDPE, plastic, recycling, manufacturing, food grade"
}
```

### **Option 2: Multipart Form Data (With Image)**
```javascript
// Headers:
Content-Type: multipart/form-data
Authorization: Bearer YOUR_ACCESS_TOKEN

// Form Data Fields:
title: Premium HDPE Material - High Quality
description: High-quality HDPE material perfect for manufacturing applications. Clean, sorted, and ready for processing. This material comes from post-industrial waste and has been thoroughly cleaned and prepared for use in various manufacturing processes.
keywords: HDPE, plastic, recycling, manufacturing, food grade
material_image: [FILE_UPLOAD - Select image file]
```

### **Option 3: JavaScript/React Example with Image**
```javascript
const formData = new FormData();
formData.append('title', 'Premium HDPE Material - High Quality');
formData.append('description', 'High-quality HDPE material perfect for manufacturing applications. Clean, sorted, and ready for processing. This material comes from post-industrial waste and has been thoroughly cleaned and prepared for use in various manufacturing processes.');
formData.append('keywords', 'HDPE, plastic, recycling, manufacturing, food grade');

// Add image file if selected
if (selectedImageFile) {
  formData.append('material_image', selectedImageFile);
}

const response = await fetch(`/api/ads/${adId}/step/8/`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    // DON'T set Content-Type header - let browser set it for multipart/form-data
  },
  body: formData
});
```

## ✅ **Success Response**
```javascript
{
  "message": "Material ad completed successfully! Your material is now listed for auction.",
  "step": 8,
  "data": {
    "id": 24,
    "title": "Premium HDPE Material - High Quality",
    "description": "High-quality HDPE material perfect for manufacturing applications...",
    "keywords": "HDPE, plastic, recycling, manufacturing, food grade",
    "material_image": "/media/material_images/image_filename.jpg",  // URL to uploaded image
    "current_step": 8,
    "is_complete": true
  },
  "step_completion_status": {
    "1": true,
    "2": true,
    "3": true,
    "4": true,
    "5": true,
    "6": true,
    "7": true,
    "8": true
  },
  "next_incomplete_step": null,
  "is_complete": true
}
```

## ❌ **Error Responses**

### **Validation Errors (400 Bad Request)**
```javascript
{
  "error": "Validation failed",
  "details": {
    "title": ["Title must be at least 10 characters long."],
    "description": ["Description must be at least 50 characters long."]
  }
}
```

### **Common Validation Errors:**

#### **Title Too Short:**
```javascript
// Request:
{
  "title": "Short",  // Only 5 characters
  "description": "Valid description that is definitely longer than fifty characters to pass validation requirements.",
}

// Response:
{
  "error": "Validation failed",
  "details": {
    "title": ["Title must be at least 10 characters long."]
  }
}
```

#### **Description Too Short:**
```javascript
// Request:
{
  "title": "Valid Title Here",
  "description": "Too short",  // Only 9 characters
}

// Response:
{
  "error": "Validation failed",
  "details": {
    "description": ["Description must be at least 50 characters long."]
  }
}
```

#### **Both Fields Invalid:**
```javascript
// Request:
{
  "title": "Short",
  "description": "Also short",
}

// Response:
{
  "error": "Validation failed",
  "details": {
    "title": ["Title must be at least 10 characters long."],
    "description": ["Description must be at least 50 characters long."]
  }
}
```

#### **Image Upload Error:**
```javascript
// When uploading invalid file type:
{
  "error": "Validation failed",
  "details": {
    "material_image": ["Upload a valid image. The file you uploaded was either not an image or a corrupted image."]
  }
}
```

## 🛠️ **Frontend Implementation Examples**

### **React Hook Example:**
```javascript
import React, { useState } from 'react';

const Step8Form = ({ adId, accessToken, onSuccess }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    keywords: ''
  });
  const [imageFile, setImageFile] = useState(null);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type client-side
      const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      if (validTypes.includes(file.type)) {
        setImageFile(file);
        setErrors(prev => ({ ...prev, material_image: null }));
      } else {
        setErrors(prev => ({ 
          ...prev, 
          material_image: 'Please select a valid image file (JPEG, PNG, GIF, WebP)' 
        }));
        e.target.value = ''; // Clear the input
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.title || formData.title.trim().length < 10) {
      newErrors.title = 'Title must be at least 10 characters long';
    }
    
    if (!formData.description || formData.description.trim().length < 50) {
      newErrors.description = 'Description must be at least 50 characters long';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    
    try {
      const submitData = new FormData();
      submitData.append('title', formData.title.trim());
      submitData.append('description', formData.description.trim());
      
      if (formData.keywords.trim()) {
        submitData.append('keywords', formData.keywords.trim());
      }
      
      if (imageFile) {
        submitData.append('material_image', imageFile);
      }

      const response = await fetch(`/api/ads/${adId}/step/8/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          // Don't set Content-Type for FormData
        },
        body: submitData
      });

      const result = await response.json();

      if (response.ok) {
        onSuccess(result);
      } else {
        if (result.details) {
          setErrors(result.details);
        } else {
          setErrors({ general: result.error || 'An error occurred' });
        }
      }
    } catch (error) {
      setErrors({ general: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} encType="multipart/form-data">
      <div>
        <label htmlFor="title">Title *</label>
        <input
          type="text"
          id="title"
          name="title"
          value={formData.title}
          onChange={handleInputChange}
          maxLength={255}
          placeholder="Enter a descriptive title (minimum 10 characters)"
          className={errors.title ? 'error' : ''}
        />
        {errors.title && <span className="error-message">{errors.title}</span>}
        <div className="char-count">{formData.title.length}/255 characters</div>
      </div>

      <div>
        <label htmlFor="description">Description *</label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleInputChange}
          rows={5}
          placeholder="Provide a detailed description of your material (minimum 50 characters)"
          className={errors.description ? 'error' : ''}
        />
        {errors.description && <span className="error-message">{errors.description}</span>}
        <div className="char-count">{formData.description.length} characters (minimum 50)</div>
      </div>

      <div>
        <label htmlFor="keywords">Keywords (Optional)</label>
        <input
          type="text"
          id="keywords"
          name="keywords"
          value={formData.keywords}
          onChange={handleInputChange}
          maxLength={500}
          placeholder="Enter keywords separated by commas (e.g., HDPE, plastic, recycling)"
        />
        <div className="char-count">{formData.keywords.length}/500 characters</div>
      </div>

      <div>
        <label htmlFor="material_image">Material Image (Optional)</label>
        <input
          type="file"
          id="material_image"
          name="material_image"
          accept="image/*"
          onChange={handleImageChange}
          className={errors.material_image ? 'error' : ''}
        />
        {errors.material_image && <span className="error-message">{errors.material_image}</span>}
        <div className="help-text">Supported formats: JPEG, PNG, GIF, WebP</div>
      </div>

      {errors.general && (
        <div className="error-message general-error">{errors.general}</div>
      )}

      <button type="submit" disabled={loading}>
        {loading ? 'Completing Ad...' : 'Complete Ad Creation'}
      </button>
    </form>
  );
};

export default Step8Form;
```

### **Vue.js Example:**
```javascript
// Vue.js component for Step 8
<template>
  <form @submit.prevent="handleSubmit" enctype="multipart/form-data">
    <div class="form-group">
      <label for="title">Title *</label>
      <input
        type="text"
        id="title"
        v-model="form.title"
        @input="clearError('title')"
        maxlength="255"
        placeholder="Enter a descriptive title (minimum 10 characters)"
        :class="{ error: errors.title }"
      />
      <span v-if="errors.title" class="error-message">{{ errors.title }}</span>
      <div class="char-count">{{ form.title.length }}/255 characters</div>
    </div>

    <div class="form-group">
      <label for="description">Description *</label>
      <textarea
        id="description"
        v-model="form.description"
        @input="clearError('description')"
        rows="5"
        placeholder="Provide a detailed description (minimum 50 characters)"
        :class="{ error: errors.description }"
      ></textarea>
      <span v-if="errors.description" class="error-message">{{ errors.description }}</span>
      <div class="char-count">{{ form.description.length }} characters (minimum 50)</div>
    </div>

    <div class="form-group">
      <label for="keywords">Keywords (Optional)</label>
      <input
        type="text"
        id="keywords"
        v-model="form.keywords"
        maxlength="500"
        placeholder="Keywords separated by commas"
      />
      <div class="char-count">{{ form.keywords.length }}/500 characters</div>
    </div>

    <div class="form-group">
      <label for="material_image">Material Image (Optional)</label>
      <input
        type="file"
        id="material_image"
        @change="handleImageChange"
        accept="image/*"
        :class="{ error: errors.material_image }"
      />
      <span v-if="errors.material_image" class="error-message">{{ errors.material_image }}</span>
      <div class="help-text">Supported: JPEG, PNG, GIF, WebP</div>
    </div>

    <button type="submit" :disabled="loading">
      {{ loading ? 'Completing Ad...' : 'Complete Ad Creation' }}
    </button>
  </form>
</template>

<script>
export default {
  props: ['adId', 'accessToken'],
  data() {
    return {
      form: {
        title: '',
        description: '',
        keywords: ''
      },
      imageFile: null,
      errors: {},
      loading: false
    };
  },
  methods: {
    clearError(field) {
      if (this.errors[field]) {
        this.$set(this.errors, field, null);
      }
    },
    
    handleImageChange(event) {
      const file = event.target.files[0];
      if (file) {
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (validTypes.includes(file.type)) {
          this.imageFile = file;
          this.clearError('material_image');
        } else {
          this.$set(this.errors, 'material_image', 'Please select a valid image file');
          event.target.value = '';
        }
      }
    },
    
    validateForm() {
      const errors = {};
      
      if (!this.form.title || this.form.title.trim().length < 10) {
        errors.title = 'Title must be at least 10 characters long';
      }
      
      if (!this.form.description || this.form.description.trim().length < 50) {
        errors.description = 'Description must be at least 50 characters long';
      }
      
      this.errors = errors;
      return Object.keys(errors).length === 0;
    },
    
    async handleSubmit() {
      if (!this.validateForm()) return;
      
      this.loading = true;
      
      try {
        const formData = new FormData();
        formData.append('title', this.form.title.trim());
        formData.append('description', this.form.description.trim());
        
        if (this.form.keywords.trim()) {
          formData.append('keywords', this.form.keywords.trim());
        }
        
        if (this.imageFile) {
          formData.append('material_image', this.imageFile);
        }

        const response = await fetch(`/api/ads/${this.adId}/step/8/`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${this.accessToken}`
          },
          body: formData
        });

        const result = await response.json();

        if (response.ok) {
          this.$emit('success', result);
        } else {
          this.errors = result.details || { general: result.error };
        }
      } catch (error) {
        this.errors = { general: 'Network error. Please try again.' };
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

## 🎯 **Key Points for Frontend Implementation**

### **1. Content-Type Headers:**
- **With Image:** Use `multipart/form-data` (don't set Content-Type manually)
- **Without Image:** Use `application/json`

### **2. Form Validation:**
- **Client-side validation** for better UX
- **Server-side validation** is final authority
- **Real-time feedback** as user types

### **3. Image Handling:**
- **Accept attribute:** `accept="image/*"` for file input
- **Client-side validation:** Check file type before upload
- **Preview functionality:** Show selected image preview
- **File size considerations:** Check file size if needed

### **4. Error Handling:**
- **Field-specific errors:** Show errors next to relevant fields
- **General errors:** Network issues, server errors
- **Clear errors:** When user starts correcting

### **5. Success Handling:**
- **Ad completion confirmation**
- **Redirect to ad listing or dashboard**
- **Show success message**

## ✅ **Testing Your Implementation**

### **Test Case 1: Valid Data Without Image**
```bash
curl -X PUT "http://localhost:8000/api/ads/24/step/8/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Premium HDPE Material - High Quality",
    "description": "High-quality HDPE material perfect for manufacturing applications. Clean, sorted, and ready for processing.",
    "keywords": "HDPE, plastic, recycling, manufacturing"
  }'
```

### **Test Case 2: Valid Data With Image**
```bash
curl -X PUT "http://localhost:8000/api/ads/24/step/8/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Premium HDPE Material - High Quality" \
  -F "description=High-quality HDPE material perfect for manufacturing applications. Clean, sorted, and ready for processing." \
  -F "keywords=HDPE, plastic, recycling, manufacturing" \
  -F "material_image=@/path/to/your/image.jpg"
```

### **Test Case 3: Invalid Data (Short Title & Description)**
```bash
curl -X PUT "http://localhost:8000/api/ads/24/step/8/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Short",
    "description": "Too short"
  }'
```

---

**Follow this guide to ensure successful Step 8 completion and avoid validation errors!** 