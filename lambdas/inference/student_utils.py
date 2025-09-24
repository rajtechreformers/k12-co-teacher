import yaml
import os

def get_students_data_2(student_profiles):
    """Extract ALL students' data using dynamic configuration (GENERAL CHAT)"""
    config = load_profile_config()
    mapping = {}

    for profile in student_profiles:
        item = profile.get("body", {}).get("Item", {})
        
        # Get student name
        first = item.get("first_name", "").strip().title()
        last = item.get("last_name", "").strip().title()
        full_name = f"{first} {last}".strip() or "Unknown Student"

        student_data = {}
        
        # Extract disabilities if enabled in YAML config
        disabilities_config = config.get('disabilities', {})
        if disabilities_config.get('enabled', True):
            disabilities = item.get(disabilities_config.get('field', 'disabilities'), [])
            if isinstance(disabilities, list):
                disability_names = []
                for d in disabilities:
                    if isinstance(d, dict):
                        name = d.get("name", "").strip()
                        if name:
                            disability_names.append(name)
                student_data["disabilities"] = disability_names
        
        # Extract accommodations if enabled in YAML config
        accommodations_config = config.get('accommodations', {})
        if accommodations_config.get('enabled', True):
            accommodations = item.get(accommodations_config.get('field', 'accommodations'), [])
            accommodation_list = []
            for a in accommodations:
                if isinstance(a, dict) and 'S' in a:
                    accommodation_list.append(a['S'].strip())
                elif isinstance(a, str):
                    accommodation_list.append(a.strip())
            student_data["accommodations"] = accommodation_list
        
        # Extract other enabled profile fields
        # this can be changed in the future to only include additional fields that client wants to consider for ALL students
        # for field_config in config.get('profile_fields', []):
        #     if field_config.get('enabled', True):
        #         field_name = field_config['field']
        #         if field_name in item and field_name not in ['disabilities', 'accommodations']:
        #             student_data[field_name] = item[field_name]
        mapping[full_name] = student_data
    return mapping

def load_profile_config():
    """Load student profile configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), 'student_profile_config.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Warning: Could not load profile config: {e}")
        return get_default_config()

def get_default_config():
    """Fallback configuration if YAML file is not available"""
    return {
        'basic_info': [
            {'field': 'first_name', 'display_name': 'First Name', 'required': True, 'fallback': 'Unknown'},
            {'field': 'last_name', 'display_name': 'Last Name', 'required': True, 'fallback': ''},
            {'field': 'grade_level', 'display_name': 'Grade', 'required': False, 'fallback': 'N/A'},
            {'field': 'age', 'display_name': 'Age', 'required': False, 'fallback': 'N/A'}
        ],
        'profile_fields': [
            {'field': 'disabilities', 'display_name': 'Disabilities', 'enabled': True, 'format': 'list', 'fallback': 'None listed'},
            {'field': 'accommodations', 'display_name': 'Accommodations', 'enabled': True, 'format': 'list', 'fallback': 'None listed'}
        ],
        'formatting': {'section_separator': '---', 'list_bullet': '- ', 'max_list_items': 10}
    }

def format_field_value(value, field_config, profile, teacher_id=None):
    """
    Format a student profile field according to the dynamic configuration.

    Args:
        value: The raw field value from the profile (string, list, dict, etc.)
        
        field_config: Dict containing display rules for this field. Keys may include:
            - format: one of {"text", "list", "structured", "dynamic"} (default "text")
                * "text":       Plain string/number display. Falls back to `fallback`.
                * "list":       Render lists as bullet points. Unwraps DynamoDB {"S": "..."} dicts.
                * "structured": Render dicts or list-of-dicts in "Key: Value" or
                                "{field1} ({field2}, {field3})" style.
                                Supports `extract_fields` to pick specific keys.
                * "dynamic":    Special case for teacher-specific comments.
                                Looks up by teacher_id in a dict of comments.
            - fallback: String to display if value is empty or missing.
            - list_bullet: Prefix for list items (default "- ").
            - max_list_items: Maximum number of list items to include.
            - extract_fields: List of keys to extract from structured dicts.
        
        profile: The entire normalized profile dict (not always used).
        
        teacher_id: Optional; required for "dynamic" format (e.g., teacherComments).
    """
    
    # If no value, return fallback immediately
    if not value and field_config.get('fallback'):
        return field_config['fallback']
    
    format_type = field_config.get('format', 'text')
    bullet = field_config.get('list_bullet', '- ')
    # LIST FORMAT
    if format_type == 'list':
        if isinstance(value, list):
            items = []
            for item in value[:field_config.get('max_list_items', 10)]:
                if isinstance(item, dict):
                    # DynamoDB wrapper: {"S": "..."}
                    if 'S' in item:
                        items.append(f"{bullet}{item['S']}")
                    # Structured dict with selected fields
                    elif field_config.get('extract_fields'):
                        parts = []
                        for field in field_config['extract_fields']:
                            if field in item and item[field]:
                                parts.append(str(item[field]))
                        if parts:
                            items.append(f"{bullet}{': '.join(parts)}")
                else:
                    items.append(f"{bullet}{str(item)}")
            return '\n'.join(items) if items else field_config.get('fallback', 'None listed')
        else:
            return f"{bullet}{str(value)}"

    # STRUCTURED FORMAT
    elif format_type == 'structured':
        if isinstance(value, dict):
            # Render each key: value pair
            items = []
            extract_fields = field_config.get('extract_fields', [])
            for key, val in value.items():
                if extract_fields and key not in extract_fields:
                    continue
                items.append(f"{bullet}{key.title()}: {val}")
            return '\n'.join(items) if items else field_config.get('fallback', 'N/A')
        
        elif isinstance(value, list):
            # Render each dict in list using extract_fields
            items = []
            for item in value:
                if isinstance(item, dict):
                    parts = []
                    for field in field_config.get('extract_fields', []):
                        if field in item and item[field]:
                            parts.append(str(item[field]))
                    if parts:
                        if len(parts) > 1:
                            items.append(f"{bullet}{parts[0]} ({', '.join(parts[1:])})")
                        else:
                            items.append(f"{bullet}{parts[0]}")
            return '\n'.join(items) if items else field_config.get('fallback', 'None listed')
    
    # DYNAMIC FORMAT (teacher-specific comments)
    elif format_type == 'dynamic' and teacher_id:
        if isinstance(value, dict) and teacher_id in value:
            comments = value[teacher_id]
            if isinstance(comments, list):
                return '\n'.join(f"{bullet}{comment}" for comment in comments)
            else:
                return str(comments)
        return field_config.get('fallback', 'No comments yet')
    
    # TEXT FORMAT (default)
    return str(value) if value else field_config.get('fallback', 'N/A')


def format_student_profile_2(profile, teacher_id=None):
    """Format student profile using dynamic configuration"""
    config = load_profile_config()
    sections = []
    
    # Basic info section
    basic_info = []
    for field_config in config.get('basic_info', []):
        field_name = field_config['field']
        display_name = field_config['display_name']
        value = profile.get(field_name, field_config.get('fallback', 'N/A'))
        basic_info.append(f"{display_name}: {value}")
    
    if basic_info:
        sections.append('\n'.join(basic_info))
    
    separator = config.get('formatting', {}).get('section_separator', '---')
    
    # All profile fields - completely dynamic based on YAML config
    for field_config in config.get('profile_fields', []):
        if field_config.get('enabled', True):
            field_name = field_config['field']
            display_name = field_config['display_name']
            value = profile.get(field_name)
            
            if value or field_config.get('fallback'):
                formatted_value = format_field_value(value, field_config, profile, teacher_id)
                sections.append(f"**{display_name}**\n{formatted_value}")
    
    return f"\n\n{separator}\n\n".join(sections)
