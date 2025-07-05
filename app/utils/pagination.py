"""
Pagination utilities
"""

from typing import List, Dict, Any, Tuple
from math import ceil

from app.models.video import PaginationInfo


def paginate_results(
    items: List[Dict[str, Any]], 
    total_count: int, 
    page: int, 
    per_page: int
) -> Tuple[List[Dict[str, Any]], PaginationInfo]:
    """
    Paginate results and return pagination info
    
    Args:
        items: List of items for current page
        total_count: Total number of items
        page: Current page number
        per_page: Items per page
        
    Returns:
        Tuple of (items, pagination_info)
    """
    total_pages = ceil(total_count / per_page) if total_count > 0 else 1
    
    pagination_info = PaginationInfo(
        page=page,
        per_page=per_page,
        total_count=total_count,
        total_pages=total_pages
    )
    
    return items, pagination_info


def get_pagination_params(page: int = 1, per_page: int = 10) -> Tuple[int, int]:
    """
    Validate and return pagination parameters
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (validated_page, validated_per_page)
    """
    # Validate page
    if page < 1:
        page = 1
    
    # Validate per_page
    if per_page < 1:
        per_page = 10
    elif per_page > 100:  # Max limit
        per_page = 100
    
    return page, per_page


def calculate_skip(page: int, per_page: int) -> int:
    """
    Calculate skip value for database queries
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Skip value for database query
    """
    return (page - 1) * per_page