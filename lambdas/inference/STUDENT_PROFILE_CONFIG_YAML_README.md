# Student Profile Configuration Guide

This guide explains how to customize the `student_profile_config.yaml` file to control what student information gets included in AI inference without modifying any code.

## Overview

The YAML configuration file allows you to:
- Enable/disable any student profile field
- Add new custom fields
- Control how fields are formatted and displayed
- Set fallback values for missing data

## Configuration Structure

```yaml
# Basic student information (always included)
basic_info:
  - field: "first_name"
    display_name: "First Name"
    required: true
    fallback: "Unknown"

# All profile fields - customers can enable/disable or add new ones
profile_fields:
  - field: "field_name_in_database"
    display_name: "Human Readable Name"
    enabled: true/false
    format: "text|list|structured|dynamic"
    fallback: "Default value if missing"
    extract_fields: ["field1", "field2"]  # Optional: for structured data

# Formatting preferences
formatting:
  section_separator: "---"
  list_bullet: "- "
  max_list_items: 10
```

## Field Configuration Options

### Required Fields
- `field`: Database field name (must match your DynamoDB data)
- `display_name`: Human-readable name shown in output
- `enabled`: `true` to include, `false` to exclude

### Format Types

#### `text` - Simple text display
```yaml
- field: "behavioral_notes"
  display_name: "Behavioral Notes"
  enabled: true
  format: "text"
  fallback: "None"
```

#### `list` - Bullet point lists
```yaml
- field: "accommodations"
  display_name: "Accommodations"
  enabled: true
  format: "list"
  fallback: "None listed"
```

#### `structured` - Complex data with specific fields
```yaml
- field: "services"
  display_name: "Services"
  enabled: true
  format: "structured"
  extract_fields: ["type", "frequency", "start_date"]
  fallback: "None listed"
```

#### `dynamic` - Teacher-specific data
```yaml
- field: "teacherComments"
  display_name: "Teacher Comments"
  enabled: true
  format: "dynamic"
  fallback: "No comments yet"
```

## How to Add New Fields

1. **Add to your DynamoDB data** - Ensure the field exists in your student profiles
2. **Add to YAML configuration**:
```yaml
profile_fields:
  # ... existing fields ...
  - field: "emergency_contact"
    display_name: "Emergency Contact"
    enabled: true
    format: "text"
    fallback: "Not provided"
```
3. **Deploy** - The field will automatically appear in student profiles

## Common Use Cases

### Enable/Disable Existing Fields
```yaml
# Disable a field you don't need
- field: "learning_styles"
  enabled: false

# Enable a field that was disabled
- field: "behavioral_notes"
  enabled: true
```

### Add Medical Information
```yaml
- field: "medical_alerts"
  display_name: "Medical Alerts"
  enabled: true
  format: "list"
  fallback: "None"

- field: "medications"
  display_name: "Current Medications"
  enabled: true
  format: "list"
  fallback: "None listed"
```

### Add Contact Information
```yaml
- field: "emergency_contact"
  display_name: "Emergency Contact"
  enabled: true
  format: "text"
  fallback: "Not provided"

- field: "parent_email"
  display_name: "Parent Email"
  enabled: true
  format: "text"
  fallback: "Not provided"
```

### Add Transportation Details
```yaml
- field: "transportation"
  display_name: "Transportation"
  enabled: true
  format: "text"
  fallback: "Parent pickup"

- field: "bus_route"
  display_name: "Bus Route"
  enabled: false
  format: "text"
  fallback: "N/A"
```

## Best Practices

1. **Start with core fields enabled**: `disabilities`, `accommodations`, `iep_goals`
2. **Use descriptive display names**: "Emergency Contact" not "emerg_contact"
3. **Set appropriate fallbacks**: Use "None" or "Not provided" rather than empty strings

## Example: School District Customization

```yaml
profile_fields:
  # Core IEP fields (always enabled)
  - field: "disabilities"
    display_name: "Disabilities"
    enabled: true
    format: "list"
    fallback: "None listed"
  
  - field: "accommodations"
    display_name: "Accommodations"
    enabled: true
    format: "list"
    fallback: "None listed"
  
  # District-specific fields
  - field: "district_id"
    display_name: "District ID"
    enabled: true
    format: "text"
    fallback: "Not assigned"
  
  - field: "lunch_program"
    display_name: "Lunch Program"
    enabled: true
    format: "text"
    fallback: "Regular"
  
  # Optional fields (disabled by default)
  - field: "previous_schools"
    display_name: "Previous Schools"
    enabled: false
    format: "list"
    fallback: "None listed"
```

## Deployment

After modifying the YAML file:
1. Save your changes
2. Deploy the Lambda function with the updated configuration
3. Test with sample data to ensure fields appear correctly

The system will automatically use your new configuration without any code changes required.