# Step 2: Material Specifications API Guide

This guide covers the updated Step 2 Material Specifications API that matches the UI form design.

## 🎯 Overview

Step 2 allows users to specify detailed material characteristics including:
- **Material Grade**: Virgin Grade, Industrial Grade, Food Grade, etc.
- **Color**: Natural/Clear, White, Black, Red, etc.
- **Material Form**: Pellets/Granules, Flakes, Regrind, Sheets, etc.
- **Additional Specifications**: Custom technical details

## 📋 API Endpoints

### 1. Get Specification Choices

**Endpoint:** `GET /api/category/specification-choices/`

**Description:** Returns all available choices for the specification form fields.

**Response:**
```json
{
  "message": "Specification choices retrieved successfully",
  "data": {
    "material_grades": [
      {"value": "virgin_grade", "label": "Virgin Grade"},
      {"value": "industrial_grade", "label": "Industrial Grade"},
      {"value": "food_grade", "label": "Food Grade"},
      {"value": "medical_grade", "label": "Medical Grade"},
      {"value": "automotive_grade", "label": "Automotive Grade"},
      {"value": "electrical_grade", "label": "Electrical Grade"},
      {"value": "recycled_grade", "label": "Recycled Grade"}
    ],
    "material_colors": [
      {"value": "Natural/Clear", "label": "Natural/Clear"},
      {"value": "White", "label": "White"},
      {"value": "Black", "label": "Black"},
      {"value": "Red", "label": "Red"},
      {"value": "Blue", "label": "Blue"},
      {"value": "Green", "label": "Green"},
      {"value": "Yellow", "label": "Yellow"},
      {"value": "Orange", "label": "Orange"},
      {"value": "Purple", "label": "Purple"},
      {"value": "Brown", "label": "Brown"},
      {"value": "Gray", "label": "Gray"},
      {"value": "Mixed Colors", "label": "Mixed Colors"},
      {"value": "Custom Color", "label": "Custom Color"}
    ],
    "material_forms": [
      {"value": "pellets_granules", "label": "Pellets/Granules"},
      {"value": "flakes", "label": "Flakes"},
      {"value": "regrind", "label": "Regrind"},
      {"value": "sheets", "label": "Sheets"},
      {"value": "film", "label": "Film"},
      {"value": "parts_components", "label": "Parts/Components"},
      {"value": "powder", "label": "Powder"},
      {"value": "fiber", "label": "Fiber"}
    ]
  }
}
```

### 2. Update Ad Step 2

**Endpoint:** `PUT /api/ads/{ad_id}/step/2/`

**Description:** Updates material specifications for an ad.

**Request Body:**
```json
{
  "specification_color": "Natural/Clear",
  "specification_material_grade": "virgin_grade", 
  "specification_material_form": "pellets_granules",
  "specification_additional": "Melt Flow Index: 2.5, Density: 0.95 g/cm³, FDA approved"
}
```

**Field Descriptions:**
- `specification_color` *(optional)*: Material color choice value
- `specification_material_grade` *(optional)*: Material grade choice value  
- `specification_material_form` *(optional)*: Material form choice value
- `specification_additional` *(optional)*: Free-text additional specifications

**Validation Rules:**
- At least ONE specification field must be provided
- Choice values must match the available options from the choices endpoint
- Invalid choice values will return validation errors

**Success Response (200):**
```json
{
  "message": "Step 2 updated successfully",
  "step": 2,
  "data": {
    "id": 14,
    "specification": {
      "id": 5,
      "Category": 2,
      "category_name": "Plastics",
      "color": "Natural/Clear",
      "color_display": "Natural/Clear",
      "material_grade": "virgin_grade",
      "material_grade_display": "Virgin Grade",
      "material_form": "pellets_granules", 
      "material_form_display": "Pellets/Granules",
      "additional_specifications": "Melt Flow Index: 2.5, Density: 0.95 g/cm³, FDA approved"
    },
    "additional_specifications": null,
    "current_step": 3
  },
  "step_completion_status": {
    "1": true,
    "2": true,
    "3": false,
    // ... rest of steps
  },
  "next_incomplete_step": 3,
  "is_complete": false
}
```

**Error Response (400):**
```json
{
  "specification_color": ["'InvalidColor' is not a valid color choice."],
  "non_field_errors": ["At least one specification field must be provided."]
}
```

## 🎨 Frontend Implementation Guide

### 1. Load Specification Choices

```javascript
// Fetch choices when component loads
const loadSpecificationChoices = async () => {
  try {
    const response = await fetch('/api/category/specification-choices/');
    const data = await response.json();
    
    setMaterialGrades(data.data.material_grades);
    setMaterialColors(data.data.material_colors);
    setMaterialForms(data.data.material_forms);
  } catch (error) {
    console.error('Failed to load choices:', error);
  }
};
```

### 2. Form State Management

```javascript
const [formData, setFormData] = useState({
  specification_color: '',
  specification_material_grade: '',
  specification_material_form: '',
  specification_additional: ''
});

const [errors, setErrors] = useState({});
```

### 3. Handle Form Submission

```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  
  try {
    const response = await fetch(`/api/ads/${adId}/step/2/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(formData)
    });
    
    if (response.ok) {
      const result = await response.json();
      // Move to next step
      router.push(`/ads/${adId}/step/3`);
    } else {
      const errorData = await response.json();
      setErrors(errorData);
    }
  } catch (error) {
    console.error('Submission failed:', error);
  }
};
```

### 4. Choice Selection Components

```javascript
// Material Grade Selection
<div className="form-group">
  <label>Material Grade</label>
  <div className="choice-grid">
    {materialGrades.map(grade => (
      <button
        key={grade.value}
        type="button"
        className={`choice-btn ${formData.specification_material_grade === grade.value ? 'selected' : ''}`}
        onClick={() => setFormData(prev => ({
          ...prev,
          specification_material_grade: grade.value
        }))}
      >
        {grade.label}
      </button>
    ))}
  </div>
</div>

// Color Selection  
<div className="form-group">
  <label>Color</label>
  <div className="choice-grid">
    {materialColors.map(color => (
      <button
        key={color.value}
        type="button"
        className={`choice-btn ${formData.specification_color === color.value ? 'selected' : ''}`}
        onClick={() => setFormData(prev => ({
          ...prev,
          specification_color: color.value
        }))}
      >
        {color.label}
      </button>
    ))}
  </div>
</div>

// Material Form Selection
<div className="form-group">
  <label>Material Form</label>
  <div className="choice-grid">
    {materialForms.map(form => (
      <button
        key={form.value}
        type="button"
        className={`choice-btn ${formData.specification_material_form === form.value ? 'selected' : ''}`}
        onClick={() => setFormData(prev => ({
          ...prev,
          specification_material_form: form.value
        }))}
      >
        {form.label}
      </button>
    ))}
  </div>
</div>

// Additional Specifications
<div className="form-group">
  <label>Additional Specifications</label>
  <textarea
    placeholder="e.g., Melt Flow Index: 2.5, Density: 0.95 g/cm³"
    value={formData.specification_additional}
    onChange={(e) => setFormData(prev => ({
      ...prev,
      specification_additional: e.target.value
    }))}
  />
</div>
```

## ✅ Validation Summary

### Required Fields
- **At least one** of the following must be provided:
  - `specification_color`
  - `specification_material_grade` 
  - `specification_material_form`
  - `specification_additional`

### Choice Validation
- All choice values must match the available options
- Invalid choices return specific error messages
- Choice values are case-sensitive

### Error Handling
- Field-specific errors for invalid choices
- General validation errors for missing required data
- Clear error messages for user guidance

## 🎯 Key Features

1. **Flexible Specification**: Users can specify any combination of grade, color, form, and additional details
2. **Validation**: Robust server-side validation ensures data integrity
3. **User-Friendly**: Clear choice options with human-readable labels
4. **Extensible**: Easy to add new specification types or choices
5. **API-First**: All choices come from the API, not hardcoded in frontend

This implementation provides a robust, validated, and user-friendly material specification system that matches the UI design requirements. 