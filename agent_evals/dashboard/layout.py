"""
Dashboard layout structure.

Defines the main layout of the dashboard with header, sidebar, and
main content area. Responsive design supporting mobile and desktop.
"""

from dash import html, dcc
from agent_evals.dashboard.config import DashboardConfig


def create_header(config: DashboardConfig) -> html.Header:
    """Create dashboard header component.
    
    Args:
        config: Dashboard configuration
        
    Returns:
        Header HTML element
    """
    colors = config.get_color_scheme()
    
    return html.Header(
        [
            html.Div(
                [
                    # Logo and title
                    html.Div(
                        [
                            html.H1(
                                config.app_title,
                                style={
                                    "margin": 0,
                                    "padding": "12px 20px",
                                    "fontSize": "20px",
                                    "fontWeight": "bold",
                                    "color": colors["text_primary"],
                                }
                            ),
                        ],
                        style={
                            "flex": 1,
                            "display": "flex",
                            "alignItems": "center",
                        }
                    ),
                    
                    # Quick stats
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("Current Score:", style={"fontWeight": "bold"}),
                                    html.Span(
                                        "--",
                                        id="header-score",
                                        style={
                                            "marginLeft": "8px",
                                            "fontSize": "16px",
                                        }
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "marginRight": "20px",
                                    "color": colors["text_secondary"],
                                }
                            ),
                            html.Div(
                                [
                                    html.Span("Trend:", style={"fontWeight": "bold"}),
                                    html.Span(
                                        "--",
                                        id="header-trend",
                                        style={
                                            "marginLeft": "8px",
                                            "fontSize": "14px",
                                        }
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "color": colors["text_secondary"],
                                }
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "20px",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "0 20px",
                    "height": f"{config.header_height}px",
                    "backgroundColor": colors["bg_secondary"],
                    "borderBottom": f"1px solid {colors['border']}",
                }
            ),
        ],
        style={
            "width": "100%",
            "backgroundColor": colors["bg_secondary"],
        }
    )


def create_sidebar(config: DashboardConfig) -> html.Aside:
    """Create sidebar navigation component.
    
    Args:
        config: Dashboard configuration
        
    Returns:
        Sidebar HTML element
    """
    colors = config.get_color_scheme()
    
    nav_item_style = {
        "padding": "12px 16px",
        "cursor": "pointer",
        "borderLeft": f"3px solid transparent",
        "transition": "all 0.3s ease",
        "color": colors["text_secondary"],
        "fontSize": "14px",
        "userSelect": "none",
    }
    
    nav_item_hover = {
        **nav_item_style,
        "backgroundColor": colors["bg_secondary"],
        "borderLeftColor": colors["primary"],
        "color": colors["text_primary"],
    }
    
    return html.Aside(
        [
            # Navigation menu
            html.Nav(
                [
                    html.Div("VIEWS", style={
                        "fontSize": "12px",
                        "fontWeight": "bold",
                        "color": colors["text_secondary"],
                        "padding": "16px 16px 8px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.5px",
                    }),
                    
                    html.Div(
                        [
                            dcc.Link(
                                "📊 Dashboard",
                                href="/",
                                id="nav-dashboard",
                                style={**nav_item_style, "display": "block"},
                                className="nav-link active",
                            ),
                            dcc.Link(
                                "📈 Trends",
                                href="/trends",
                                id="nav-trends",
                                style={**nav_item_style, "display": "block"},
                                className="nav-link",
                            ),
                            dcc.Link(
                                "✓ Requirements",
                                href="/requirements",
                                id="nav-requirements",
                                style={**nav_item_style, "display": "block"},
                                className="nav-link",
                            ),
                            dcc.Link(
                                "⚖️ Compare",
                                href="/comparison",
                                id="nav-comparison",
                                style={**nav_item_style, "display": "block"},
                                className="nav-link",
                            ),
                        ],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                        }
                    ),
                ],
                style={
                    "flex": 1,
                }
            ),
            
            # Filters section
            html.Section(
                [
                    html.Div("FILTERS", style={
                        "fontSize": "12px",
                        "fontWeight": "bold",
                        "color": colors["text_secondary"],
                        "padding": "16px 16px 12px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.5px",
                        "borderTop": f"1px solid {colors['border']}",
                    }),
                    
                    # Date range filter
                    html.Div(
                        [
                            html.Label(
                                "Date Range:",
                                style={
                                    "fontSize": "12px",
                                    "fontWeight": "bold",
                                    "marginBottom": "6px",
                                }
                            ),
                            dcc.DatePickerRange(
                                id="date-range-picker",
                                display_format="YYYY-MM-DD",
                                style={"width": "100%"},
                            ),
                        ],
                        style={
                            "padding": "0 16px 12px",
                        }
                    ),
                    
                    # Environment selector
                    html.Div(
                        [
                            html.Label(
                                "Environment:",
                                style={
                                    "fontSize": "12px",
                                    "fontWeight": "bold",
                                    "marginBottom": "6px",
                                }
                            ),
                            dcc.Dropdown(
                                id="environment-selector",
                                options=[
                                    {"label": "Development", "value": "development"},
                                    {"label": "Staging", "value": "staging"},
                                    {"label": "Production", "value": "production"},
                                ],
                                value="development",
                                style={"width": "100%"},
                            ),
                        ],
                        style={
                            "padding": "0 16px 12px",
                        }
                    ),
                ],
                style={
                    "padding": "12px 0",
                    "borderTop": f"1px solid {colors['border']}",
                }
            ),
        ],
        style={
            "width": f"{config.sidebar_width}px",
            "backgroundColor": colors["bg_secondary"],
            "borderRight": f"1px solid {colors['border']}",
            "display": "flex",
            "flexDirection": "column",
            "height": "calc(100vh - " + str(config.header_height) + "px)",
            "overflowY": "auto",
            "padding": "12px 0",
        }
    )


def create_main_content(config: DashboardConfig) -> html.Main:
    """Create main content area.
    
    Args:
        config: Dashboard configuration
        
    Returns:
        Main content HTML element
    """
    colors = config.get_color_scheme()
    
    return html.Main(
        [
            # Page content (will be updated by callbacks)
            html.Div(
                id="page-content",
                style={
                    "padding": "20px",
                    "flex": 1,
                    "overflowY": "auto",
                }
            ),
        ],
        style={
            "flex": 1,
            "display": "flex",
            "flexDirection": "column",
            "backgroundColor": colors["bg_primary"],
            "overflowY": "auto",
        }
    )


def create_layout(config: DashboardConfig) -> html.Div:
    """Create the main dashboard layout.
    
    Returns a responsive layout with:
    - Header (top navigation, quick stats)
    - Sidebar (navigation, filters)
    - Main content area (page content)
    - Footer (optional)
    
    Args:
        config: Dashboard configuration
        
    Returns:
        Root HTML element containing the entire layout
    """
    colors = config.get_color_scheme()
    
    return html.Div(
        [
            # URL for page routing
            dcc.Location(id="url", refresh=False),
            
            # Header
            create_header(config),
            
            # Main container (sidebar + content)
            html.Div(
                [
                    # Sidebar
                    create_sidebar(config),
                    
                    # Main content
                    create_main_content(config),
                ],
                style={
                    "display": "flex",
                    "flex": 1,
                    "height": "calc(100vh - " + str(config.header_height) + "px)",
                }
            ),
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "height": "100vh",
            "margin": 0,
            "padding": 0,
            "backgroundColor": colors["bg_primary"],
            "fontFamily": config.font_family,
            "color": colors["text_primary"],
        }
    )
