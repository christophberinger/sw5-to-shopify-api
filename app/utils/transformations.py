import re
import json
from typing import Any


def apply_transformation(value: Any, transformation: dict, target_field: str = "", metafield_type: str = None) -> Any:
    """
    Apply transformation rules to a value

    Transformation types:
    - direct: No transformation
    - replace: Simple string replacement
    - regex: Regex-based replacement
    - split_join: Split by one delimiter, join with another
    - custom: Custom Python code (use with caution)

    Args:
        value: The value to transform
        transformation: Dict with transformation rules
        target_field: The target field path (e.g., "metafields[].custom.vehicletypes")
        metafield_type: Optional metafield type (e.g., "list.single_line_text_field")
    """
    if value is None:
        return None

    transform_type = transformation.get('type', 'direct')

    # Convert to string for transformations
    str_value = str(value)

    if transform_type == 'direct':
        # Special case: if target is a list metafield and value contains delimiters,
        # automatically convert to JSON array
        if metafield_type and metafield_type.startswith('list.'):
            # Try common delimiters
            for delim in ['|', ',', ';']:
                if delim in str_value:
                    parts = [p.strip() for p in str_value.split(delim) if p.strip()]
                    if len(parts) > 1:
                        result = json.dumps(parts)
                        print(f"DEBUG: direct transform auto-converted to JSON array for list metafield: {result}")
                        return result
        return value

    elif transform_type == 'replace':
        find = transformation.get('find', '')
        replace = transformation.get('replace', '')
        if find:
            return str_value.replace(find, replace)
        return value

    elif transform_type == 'regex':
        pattern = transformation.get('find', '')
        replace = transformation.get('replace', '')
        if pattern:
            try:
                return re.sub(pattern, replace, str_value)
            except Exception as e:
                print(f"Regex error: {e}")
                return value
        return value

    elif transform_type == 'split_join':
        split_delim = transformation.get('split_delimiter', '')
        join_delim = transformation.get('join_delimiter', '')
        if split_delim:
            parts = str_value.split(split_delim)
            # Clean up parts (strip whitespace, remove prefixes)
            cleaned_parts = []
            for part in parts:
                part = part.strip()
                # Remove common prefixes like "Fahrzeugverwendung:"
                if ':' in part:
                    part = part.split(':', 1)[1].strip()
                if part:
                    cleaned_parts.append(part)

            # PRIORITY 1: Check if target is a list-type metafield
            # If so, ALWAYS return JSON array, regardless of join_delimiter setting
            is_list_metafield = metafield_type and metafield_type.startswith('list.')

            if is_list_metafield:
                result = json.dumps(cleaned_parts)
                print(f"DEBUG: split_join created JSON array for list metafield {target_field} (type={metafield_type}): {result}")
                return result

            # PRIORITY 2: Legacy heuristic for metafields without explicit type
            # Only applies if no join delimiter is specified
            is_metafield_target = 'metafield' in target_field.lower() and not join_delim

            if is_metafield_target:
                result = json.dumps(cleaned_parts)
                print(f"DEBUG: split_join created JSON array for metafield target {target_field}: {result}")
                return result

            # PRIORITY 3: Otherwise join with delimiter for regular fields
            result = join_delim.join(cleaned_parts)
            print(f"DEBUG: split_join joined with '{join_delim}' for regular field {target_field}: {result[:100]}")
            return result
        return value

    elif transform_type == 'custom':
        # WARNING: This executes custom code - use with caution
        custom_code = transformation.get('custom_code', '')
        if custom_code:
            try:
                # Create a safe namespace
                namespace = {'value': str_value, 're': re}
                exec(f"result = {custom_code}", namespace)
                return namespace.get('result', value)
            except Exception as e:
                print(f"Custom transformation error: {e}")
                return value
        return value

    return value
