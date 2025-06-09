# Step 8 Image Upload Guide - Frontend Implementation

## Overview

Step 8 is the final step in the ad creation process where users provide:
- **Title** (required, minimum 10 characters)
- **Description** (required, minimum 50 characters)  
- **Keywords** (optional, comma-separated)
- **Material Image** (optional, but recommended)

Upon successful completion of Step 8, the ad becomes `is_complete = true` and ready for auction.

## API Endpoint

```
PUT /api/ads/{ad_id}/step/8/
```

## Authentication

All requests require Bearer token authentication:

```javascript
headers: {
    'Authorization': 'Bearer ' + userToken
}
```

## Request Format

### Method 1: Multipart Form Data (Recommended)

This is the standard approach for file uploads.

#### JavaScript Implementation

```javascript
const uploadStep8 = async (adId, formData) => {
    const form = new FormData();
    
    // Add text fields
    form.append('title', formData.title);
    form.append('description', formData.description);
    form.append('keywords', formData.keywords || '');
    
    // Add image file (if selected)
    if (formData.imageFile) {
        form.append('material_image', formData.imageFile);
    }
    
    try {
        const response = await fetch(`/api/ads/${adId}/step/8/`, {
            method: 'PUT',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('token'),
                // Don't set Content-Type - browser will set it automatically for FormData
            },
            body: form
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('Step 8 upload error:', error);
        throw error;
    }
};

// Usage example
const handleStep8Submit = async (e) => {
    e.preventDefault();
    
    const formData = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        keywords: document.getElementById('keywords').value,
        imageFile: document.getElementById('image').files[0] // File object
    };
    
    try {
        const result = await uploadStep8(123, formData);
        console.log('Ad completed:', result);
        // Handle success (redirect, show message, etc.)
    } catch (error) {
        // Handle error (show error message, etc.)
        console.error('Error:', error.message);
    }
};
```

#### React Implementation

```jsx
import React, { useState } from 'react';

const Step8Form = ({ adId, onSuccess, onError }) => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        keywords: '',
        imageFile: null
    });
    const [loading, setLoading] = useState(false);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleFileChange = (e) => {
        setFormData(prev => ({
            ...prev,
            imageFile: e.target.files[0]
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const form = new FormData();
        form.append('title', formData.title);
        form.append('description', formData.description);
        form.append('keywords', formData.keywords);
        
        if (formData.imageFile) {
            form.append('material_image', formData.imageFile);
        }

        try {
            const response = await fetch(`/api/ads/${adId}/step/8/`, {
                method: 'PUT',
                headers: {
                    'Authorization': 'Bearer ' + localStorage.getItem('token')
                },
                body: form
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Upload failed');
            }

            const result = await response.json();
            onSuccess(result);

        } catch (error) {
            onError(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label htmlFor="title">Title *</label>
                <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    required
                    minLength={10}
                    placeholder="Enter ad title (minimum 10 characters)"
                />
            </div>

            <div>
                <label htmlFor="description">Description *</label>
                <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    required
                    minLength={50}
                    rows={5}
                    placeholder="Enter detailed description (minimum 50 characters)"
                />
            </div>

            <div>
                <label htmlFor="keywords">Keywords</label>
                <input
                    type="text"
                    id="keywords"
                    name="keywords"
                    value={formData.keywords}
                    onChange={handleInputChange}
                    placeholder="Enter keywords separated by commas"
                />
            </div>

            <div>
                <label htmlFor="image">Material Image</label>
                <input
                    type="file"
                    id="image"
                    name="material_image"
                    onChange={handleFileChange}
                    accept="image/*"
                />
            </div>

            <button type="submit" disabled={loading}>
                {loading ? 'Uploading...' : 'Complete Ad'}
            </button>
        </form>
    );
};

export default Step8Form;
```

#### HTML Form Implementation

```html
<!DOCTYPE html>
<html>
<head>
    <title>Step 8 - Complete Your Ad</title>
</head>
<body>
    <form id="step8Form" enctype="multipart/form-data">
        <div>
            <label for="title">Title *</label>
            <input type="text" id="title" name="title" required minlength="10" 
                   placeholder="Enter ad title (minimum 10 characters)">
        </div>

        <div>
            <label for="description">Description *</label>
            <textarea id="description" name="description" required minlength="50" 
                      rows="5" placeholder="Enter detailed description (minimum 50 characters)"></textarea>
        </div>

        <div>
            <label for="keywords">Keywords</label>
            <input type="text" id="keywords" name="keywords" 
                   placeholder="Enter keywords separated by commas">
        </div>

        <div>
            <label for="image">Material Image</label>
            <input type="file" id="image" name="material_image" accept="image/*">
        </div>

        <button type="submit">Complete Ad</button>
    </form>

    <script>
        document.getElementById('step8Form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const adId = 123; // Get this from your app state
            
            try {
                const response = await fetch(`/api/ads/${adId}/step/8/`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    },
                    body: formData
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Upload failed');
                }
                
                const result = await response.json();
                console.log('Success:', result);
                alert('Ad completed successfully!');
                
            } catch (error) {
                console.error('Error:', error);
                alert('Error: ' + error.message);
            }
        });
    </script>
</body>
</html>
```

### Method 2: Base64 Encoded Image (Alternative)

If you need to send as JSON (not recommended for large images):

```javascript
const convertImageToBase64 = (file) => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
};

const uploadStep8JSON = async (adId, data) => {
    let requestData = {
        title: data.title,
        description: data.description,
        keywords: data.keywords || ''
    };

    // Convert image to base64 if provided
    if (data.imageFile) {
        try {
            requestData.material_image = await convertImageToBase64(data.imageFile);
        } catch (error) {
            throw new Error('Failed to process image');
        }
    }

    const response = await fetch(`/api/ads/${adId}/step/8/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + localStorage.getItem('token')
        },
        body: JSON.stringify(requestData)
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Upload failed');
    }

    return await response.json();
};
```

## Field Validation

### Title
- **Required**: Yes
- **Minimum Length**: 10 characters
- **Type**: String

### Description  
- **Required**: Yes
- **Minimum Length**: 50 characters
- **Type**: String (textarea)

### Keywords
- **Required**: No
- **Format**: Comma-separated values
- **Example**: `"HDPE,recycling,bottles,food grade"`

### Material Image
- **Required**: No (but recommended)
- **Accepted Formats**: JPEG, PNG, GIF, WebP
- **Max Size**: Check Django settings (typically 5-10MB)
- **Upload Path**: Images stored in `/media/material_images/`

## Response Format

### Success Response (HTTP 200)

```json
{
    "message": "Material ad completed successfully! Your material is now listed for auction.",
    "step": 8,
    "data": {
        "id": 123,
        "title": "Premium HDPE Bottles - Food Grade Quality",
        "description": "High-quality HDPE milk bottles from Swedish dairy facilities...",
        "keywords": "HDPE,food grade,milk bottles,clean,recycling",
        "material_image": "/media/material_images/hdpe_bottles_20241215_123456.jpg",
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

### Error Response (HTTP 400)

```json
{
    "error": "Validation failed",
    "details": {
        "title": ["Title must be at least 10 characters long."],
        "description": ["Description must be at least 50 characters long."]
    }
}
```

## Error Handling

### Common Validation Errors

```javascript
const handleValidationErrors = (errorResponse) => {
    if (errorResponse.details) {
        // Field-specific errors
        Object.keys(errorResponse.details).forEach(field => {
            const errors = errorResponse.details[field];
            console.error(`${field}: ${errors.join(', ')}`);
            // Show error message near the field
        });
    } else {
        // General error
        console.error('Error:', errorResponse.error);
    }
};
```

### Image Upload Errors

```javascript
const handleImageErrors = (error) => {
    if (error.message.includes('file size')) {
        alert('Image file is too large. Please choose a smaller image.');
    } else if (error.message.includes('format')) {
        alert('Invalid image format. Please use JPEG, PNG, or GIF.');
    } else {
        alert('Image upload failed: ' + error.message);
    }
};
```

## Complete Example with Error Handling

```javascript
class Step8Handler {
    constructor(apiBaseUrl, authToken) {
        this.apiBaseUrl = apiBaseUrl;
        this.authToken = authToken;
    }

    async submitStep8(adId, formData) {
        const form = new FormData();
        
        // Validate required fields
        if (!formData.title || formData.title.length < 10) {
            throw new Error('Title must be at least 10 characters long');
        }
        
        if (!formData.description || formData.description.length < 50) {
            throw new Error('Description must be at least 50 characters long');
        }
        
        // Add form data
        form.append('title', formData.title.trim());
        form.append('description', formData.description.trim());
        form.append('keywords', formData.keywords || '');
        
        if (formData.imageFile) {
            // Validate image file
            if (!this.isValidImageFile(formData.imageFile)) {
                throw new Error('Please select a valid image file (JPEG, PNG, GIF)');
            }
            
            form.append('material_image', formData.imageFile);
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/ads/${adId}/step/8/`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: form
            });
            
            const responseData = await response.json();
            
            if (!response.ok) {
                if (response.status === 400) {
                    throw new Error(responseData.error || 'Validation failed');
                } else if (response.status === 401) {
                    throw new Error('Authentication required. Please log in.');
                } else if (response.status === 404) {
                    throw new Error('Ad not found');
                } else {
                    throw new Error('Server error. Please try again.');
                }
            }
            
            return responseData;
            
        } catch (error) {
            if (error instanceof TypeError) {
                throw new Error('Network error. Please check your connection.');
            }
            throw error;
        }
    }
    
    isValidImageFile(file) {
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        return validTypes.includes(file.type);
    }
}

// Usage
const step8Handler = new Step8Handler('http://localhost:8000', userToken);

const handleFormSubmit = async (formData) => {
    try {
        const result = await step8Handler.submitStep8(adId, formData);
        
        // Success handling
        console.log('Ad completed successfully:', result);
        
        // Redirect to ad detail page or show success message
        window.location.href = `/ads/${result.data.id}`;
        
    } catch (error) {
        // Error handling
        console.error('Step 8 submission failed:', error.message);
        
        // Show error message to user
        document.getElementById('error-message').textContent = error.message;
        document.getElementById('error-message').style.display = 'block';
    }
};
```

## Image Preview Feature

Add image preview functionality:

```javascript
const handleImagePreview = (fileInput, previewElement) => {
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        
        if (file) {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                previewElement.src = e.target.result;
                previewElement.style.display = 'block';
            };
            
            reader.readAsDataURL(file);
        } else {
            previewElement.style.display = 'none';
        }
    });
};

// Usage
const imageInput = document.getElementById('image');
const imagePreview = document.getElementById('image-preview');
handleImagePreview(imageInput, imagePreview);
```

## Testing Tips

1. **Test without image**: Ensure the form works without uploading an image
2. **Test with different image formats**: JPEG, PNG, GIF
3. **Test large images**: Verify file size limits
4. **Test validation**: Try submitting with short title/description
5. **Test network errors**: Handle connection issues gracefully

## Security Considerations

1. **Always validate file types** on the frontend (but remember backend validation is primary)
2. **Sanitize text inputs** before submission
3. **Handle authentication errors** properly
4. **Don't expose sensitive data** in error messages

This completes the Step 8 implementation guide. The ad will be marked as complete and ready for auction after successful submission. 