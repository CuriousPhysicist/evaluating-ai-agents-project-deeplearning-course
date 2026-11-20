"""
Dashboard utility functions.

Provides helper functions for common dashboard operations like
data formatting, URL routing, and component generation.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import quote, unquote


def format_score(score: float, as_percentage: bool = True) -> str:
    """Format a score for display.
    
    Args:
        score: Score value (0.0-1.0)
        as_percentage: If True, format as percentage; else as decimal
        
    Returns:
        Formatted score string
    """
    if as_percentage:
        return f"{score * 100:.1f}%"
    else:
        return f"{score:.3f}"


def format_timestamp(timestamp: str) -> str:
    """Format ISO 8601 timestamp for display.
    
    Args:
        timestamp: ISO 8601 formatted timestamp string
        
    Returns:
        Human-readable timestamp string
    """
    try:
        # Parse ISO 8601 timestamp
        if timestamp.endswith('Z'):
            dt = datetime.fromisoformat(timestamp[:-1] + '+00:00')
        else:
            dt = datetime.fromisoformat(timestamp)
        
        # Format as readable string
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return timestamp


def get_trend_arrow(trend_direction: str) -> str:
    """Get arrow emoji for trend direction.
    
    Args:
        trend_direction: One of 'improving', 'stable', 'declining'
        
    Returns:
        Arrow emoji and label
    """
    arrows = {
        'improving': '📈 Improving',
        'stable': '➡️ Stable',
        'declining': '📉 Declining',
    }
    return arrows.get(trend_direction, '❓ Unknown')


def get_score_color_code(score: float) -> str:
    """Get RGB color code for a score value.
    
    Args:
        score: Score value (0.0-1.0)
        
    Returns:
        RGB color code string (e.g., 'rgb(255, 0, 0)')
    """
    # Green (good): 0.8+
    # Amber (warning): 0.6-0.8
    # Orange (caution): 0.4-0.6
    # Red (poor): <0.4
    
    if score >= 0.8:
        return 'rgb(76, 175, 80)'  # Green
    elif score >= 0.6:
        return 'rgb(255, 193, 7)'  # Amber
    elif score >= 0.4:
        return 'rgb(255, 152, 0)'  # Orange
    else:
        return 'rgb(244, 67, 54)'  # Red


def get_score_badge_style(score: float) -> Dict[str, str]:
    """Get styling dict for score badge.
    
    Args:
        score: Score value (0.0-1.0)
        
    Returns:
        Dictionary with CSS style properties
    """
    color = get_score_color_code(score)
    
    # Extract RGB values
    rgb_match = color.replace('rgb(', '').replace(')', '').split(', ')
    r, g, b = rgb_match[0], rgb_match[1], rgb_match[2]
    
    return {
        'backgroundColor': f'rgba({r}, {g}, {b}, 0.1)',
        'color': color,
        'borderRadius': '4px',
        'padding': '8px 12px',
        'fontSize': '14px',
        'fontWeight': 'bold',
        'display': 'inline-block',
    }


def parse_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple:
    """Parse date range strings to datetime objects.
    
    Args:
        start_date: Start date string (YYYY-MM-DD format or None)
        end_date: End date string (YYYY-MM-DD format or None)
        
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    try:
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            # Default: 30 days ago
            start = datetime.now() - timedelta(days=30)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Include full day
            end = end.replace(hour=23, minute=59, second=59)
        else:
            # Default: today
            end = datetime.now()
        
        return (start, end)
    except Exception:
        # Fallback to defaults
        end = datetime.now()
        start = end - timedelta(days=30)
        return (start, end)


def build_url_path(base_path: str, params: Dict[str, Any] = None) -> str:
    """Build URL path with optional query parameters.
    
    Args:
        base_path: Base URL path (e.g., '/trends')
        params: Optional dictionary of query parameters
        
    Returns:
        Complete URL path
    """
    if not params:
        return base_path
    
    # Build query string
    query_parts = []
    for key, value in params.items():
        if value is not None:
            query_parts.append(f"{quote(str(key))}={quote(str(value))}")
    
    query_string = '&'.join(query_parts)
    
    if query_string:
        return f"{base_path}?{query_string}"
    else:
        return base_path


def parse_query_params(search_string: str) -> Dict[str, str]:
    """Parse query parameters from URL search string.
    
    Args:
        search_string: Query string (e.g., 'tab=scores&period=7d')
        
    Returns:
        Dictionary of parameters
    """
    params = {}
    
    if not search_string or not search_string.startswith('?'):
        return params
    
    search_string = search_string[1:]  # Remove leading '?'
    
    for pair in search_string.split('&'):
        if '=' in pair:
            key, value = pair.split('=', 1)
            params[unquote(key)] = unquote(value)
    
    return params


def get_days_ago(days: int) -> datetime:
    """Get datetime for N days ago.
    
    Args:
        days: Number of days in the past
        
    Returns:
        datetime object
    """
    return datetime.now() - timedelta(days=days)


def get_summary_text(scores: List[float]) -> str:
    """Get a text summary of score statistics.
    
    Args:
        scores: List of score values
        
    Returns:
        Summary text
    """
    if not scores:
        return "No data available"
    
    avg = sum(scores) / len(scores)
    min_score = min(scores)
    max_score = max(scores)
    
    return (
        f"Average: {format_score(avg)}, "
        f"Range: {format_score(min_score)} - {format_score(max_score)}"
    )


def build_breadcrumb_path(current_path: str) -> List[Dict[str, str]]:
    """Build breadcrumb navigation from current path.
    
    Args:
        current_path: Current URL path (e.g., '/trends/detail')
        
    Returns:
        List of breadcrumb items with label and href
    """
    breadcrumbs = [
        {"label": "Dashboard", "href": "/"}
    ]
    
    # Remove leading and trailing slashes
    current_path = current_path.strip('/')
    
    if not current_path:
        return breadcrumbs
    
    # Split path into segments
    segments = current_path.split('/')
    path_so_far = ""
    
    for segment in segments:
        path_so_far += f"/{segment}"
        
        # Format label (capitalize, replace hyphens)
        label = segment.replace('-', ' ').replace('_', ' ').title()
        
        breadcrumbs.append({
            "label": label,
            "href": path_so_far
        })
    
    return breadcrumbs
