"""
Utility functions for ads app
"""
from typing import List, Optional
from django.db.models import Q


def parse_multiple_ids(param_value: Optional[str]) -> List[int]:
    """
    Parse comma-separated string of IDs into a list of integers.
    
    Args:
        param_value: String like "1,2,3" or single value "1"
        
    Returns:
        List of integers or empty list if param_value is None/empty
        
    Examples:
        parse_multiple_ids("1,2,3") -> [1, 2, 3]
        parse_multiple_ids("1") -> [1]
        parse_multiple_ids("") -> []
        parse_multiple_ids(None) -> []
    """
    if not param_value or param_value.strip() == '':
        return []
    
    try:
        # Split by comma and convert to integers, filtering out invalid values
        ids = []
        for id_str in param_value.split(','):
            id_str = id_str.strip()
            if id_str:
                ids.append(int(id_str))
        return ids
    except ValueError:
        return []


def build_subcategory_filter(subcategory_ids: List[int]) -> Optional[Q]:
    """
    Build Django Q object for filtering by multiple subcategories.
    
    Args:
        subcategory_ids: List of subcategory IDs
        
    Returns:
        Q object for filtering or None if no IDs provided
        
    Examples:
        build_subcategory_filter([1, 2, 3]) -> Q(subcategory_id__in=[1, 2, 3])
        build_subcategory_filter([1]) -> Q(subcategory_id=1)
        build_subcategory_filter([]) -> None
    """
    if not subcategory_ids:
        return None
    
    if len(subcategory_ids) == 1:
        # Single subcategory - use exact match for better performance
        return Q(subcategory_id=subcategory_ids[0])
    else:
        # Multiple subcategories - use __in lookup
        return Q(subcategory_id__in=subcategory_ids)


def parse_multiple_values(param_value: Optional[str]) -> List[str]:
    """
    Parse comma-separated string values into a list of strings.
    
    Args:
        param_value: String like "value1,value2,value3" or single value "value1"
        
    Returns:
        List of strings or empty list if param_value is None/empty
        
    Examples:
        parse_multiple_values("clean,dirty") -> ["clean", "dirty"]
        parse_multiple_values("clean") -> ["clean"]
        parse_multiple_values("") -> []
        parse_multiple_values(None) -> []
    """
    if not param_value or param_value.strip() == '':
        return []
    
    # Split by comma and strip whitespace, filtering out empty values
    values = []
    for value in param_value.split(','):
        value = value.strip()
        if value:
            values.append(value)
    return values


def build_multiple_choice_filter(field_name: str, values: List[str]) -> Optional[Q]:
    """
    Build Django Q object for filtering by multiple choice values.
    
    Args:
        field_name: The field to filter on (e.g., 'origin', 'contamination')
        values: List of values to filter by
        
    Returns:
        Q object for filtering or None if no values provided
        
    Examples:
        build_multiple_choice_filter('origin', ['post_industrial', 'post_consumer']) 
        -> Q(origin__in=['post_industrial', 'post_consumer'])
    """
    if not values:
        return None
    
    if len(values) == 1:
        # Single value - use exact match
        return Q(**{field_name: values[0]})
    else:
        # Multiple values - use __in lookup
        return Q(**{f"{field_name}__in": values})

