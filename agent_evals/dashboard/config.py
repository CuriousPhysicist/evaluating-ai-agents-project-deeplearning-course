"""
Dashboard configuration system.

Provides centralized configuration for dashboard appearance, behavior,
and performance settings. All configuration can be customized via
environment variables or programmatic updates.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import os


@dataclass
class DashboardConfig:
    """Dashboard configuration settings."""

    # Application metadata
    app_title: str = "AI Agent Compliance Dashboard"
    app_version: str = "1.0.0"
    
    # Theme and styling
    theme: str = "light"  # or "dark"
    primary_color: str = "#1f77b4"  # Plotly blue
    success_color: str = "#2ca02c"  # Green
    warning_color: str = "#ff7f0e"  # Orange
    danger_color: str = "#d62728"  # Red
    neutral_color: str = "#7f7f7f"  # Gray
    
    # Layout configuration
    mobile_breakpoint: int = 768  # pixels (responsive breakpoint)
    sidebar_width: int = 250  # pixels
    header_height: int = 60  # pixels
    
    # Performance settings
    refresh_interval: int = 300  # seconds
    max_data_points: int = 100  # limit for performance
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    
    # Feature flags
    enable_dark_mode: bool = True
    enable_export: bool = True
    enable_comparison_view: bool = True
    enable_alerts: bool = True
    
    # Data settings
    default_date_range_days: int = 30
    default_environment: str = "development"
    
    # Plotly chart settings
    chart_height: int = 400  # pixels
    heatmap_height: int = 300  # pixels
    scatter_height: int = 350  # pixels
    
    # Font settings
    font_family: str = "Roboto, sans-serif"
    font_size_base: int = 14  # pixels
    
    @classmethod
    def from_env(cls) -> "DashboardConfig":
        """Create configuration from environment variables.
        
        Environment variables can override defaults:
        - DASHBOARD_THEME: light or dark
        - DASHBOARD_REFRESH_INTERVAL: seconds
        - DASHBOARD_CACHE_TTL: seconds
        - DASHBOARD_MAX_DATA_POINTS: number
        - etc.
        
        Returns:
            DashboardConfig instance with environment overrides applied
        """
        config = cls()
        
        # Apply environment variable overrides
        if theme := os.getenv("DASHBOARD_THEME"):
            config.theme = theme
            
        if refresh := os.getenv("DASHBOARD_REFRESH_INTERVAL"):
            try:
                config.refresh_interval = int(refresh)
            except ValueError:
                pass
                
        if cache_ttl := os.getenv("DASHBOARD_CACHE_TTL"):
            try:
                config.cache_ttl = int(cache_ttl)
            except ValueError:
                pass
                
        if max_points := os.getenv("DASHBOARD_MAX_DATA_POINTS"):
            try:
                config.max_data_points = int(max_points)
            except ValueError:
                pass
        
        return config
    
    def get_color_scheme(self) -> Dict[str, str]:
        """Get color scheme based on current theme.
        
        Returns:
            Dictionary mapping color roles to RGB values
        """
        if self.theme == "dark":
            return {
                "bg_primary": "#1a1a1a",
                "bg_secondary": "#2d2d2d",
                "text_primary": "#ffffff",
                "text_secondary": "#b0b0b0",
                "border": "#404040",
                "primary": self.primary_color,
                "success": self.success_color,
                "warning": self.warning_color,
                "danger": self.danger_color,
            }
        else:  # light theme
            return {
                "bg_primary": "#ffffff",
                "bg_secondary": "#f5f5f5",
                "text_primary": "#333333",
                "text_secondary": "#666666",
                "border": "#e0e0e0",
                "primary": self.primary_color,
                "success": self.success_color,
                "warning": self.warning_color,
                "danger": self.danger_color,
            }
    
    def to_plotly_template(self) -> Dict:
        """Get Plotly layout template based on configuration.
        
        Returns:
            Dictionary suitable for Plotly chart layout
        """
        colors = self.get_color_scheme()
        
        return {
            "layout": {
                "font": {"family": self.font_family, "size": self.font_size_base},
                "plot_bgcolor": colors["bg_secondary"],
                "paper_bgcolor": colors["bg_primary"],
                "font_color": colors["text_primary"],
                "title_font_size": self.font_size_base + 2,
                "xaxis": {"gridcolor": colors["border"]},
                "yaxis": {"gridcolor": colors["border"]},
            }
        }


def get_config() -> DashboardConfig:
    """Get the global dashboard configuration.
    
    Returns:
        DashboardConfig instance
    """
    return DashboardConfig.from_env()
