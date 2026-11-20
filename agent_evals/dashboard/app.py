"""
Main Dash application for the interactive dashboard.

Initializes the Dash app, sets up styling, and prepares callbacks
for interactive functionality.
"""

from dash import Dash, html
import dash_bootstrap_components as dbc
from agent_evals.dashboard.layout import create_layout
from agent_evals.dashboard.config import DashboardConfig
from agent_evals.dashboard.query_service import DashboardQueryService
from agent_evals.dashboard.data_transformer import DashboardDataTransformer


class DashboardApp:
    """Main dashboard application wrapper.
    
    Manages Dash app initialization, styling, and configuration.
    Provides methods for running the dashboard and accessing services.
    
    Attributes:
        app: Dash application instance
        config: Dashboard configuration
        query_service: Service for querying compliance data
        transformer: Service for transforming data to visualization formats
    """
    
    def __init__(self, config: DashboardConfig = None, mock_data: dict = None):
        """Initialize dashboard application.
        
        Args:
            config: Optional DashboardConfig instance (uses defaults if None)
            mock_data: Optional mock data dictionary for development
        """
        self.config = config or DashboardConfig.from_env()
        
        # Initialize services
        self.query_service = DashboardQueryService(mock_data=mock_data or {})
        self.transformer = DashboardDataTransformer(query_service=self.query_service)
        
        # Create Dash app
        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            meta_tags=[
                {"name": "viewport", "content": "width=device-width, initial-scale=1"}
            ]
        )
        
        # Set app title
        self.app.title = self.config.app_title
        
        # Create and set layout
        self.app.layout = create_layout(self.config)
        
        # Apply custom CSS
        self._apply_custom_styling()
    
    def _apply_custom_styling(self) -> None:
        """Apply custom CSS styling to the app.
        
        Includes responsive design, color themes, and mobile optimizations.
        """
        colors = self.config.get_color_scheme()
        
        # Build CSS as a string
        custom_css = f"""
        :root {{
            --primary-color: {colors['primary']};
            --success-color: {colors['success']};
            --warning-color: {colors['warning']};
            --danger-color: {colors['danger']};
            --bg-primary: {colors['bg_primary']};
            --bg-secondary: {colors['bg_secondary']};
            --text-primary: {colors['text_primary']};
            --text-secondary: {colors['text_secondary']};
            --border-color: {colors['border']};
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: {self.config.font_family};
            font-size: {self.config.font_size_base}px;
            color: var(--text-primary);
            background-color: var(--bg-primary);
        }}
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg-secondary);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--text-secondary);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-primary);
        }}
        
        /* Navigation link styling */
        .nav-link {{
            text-decoration: none;
            color: var(--text-secondary);
            transition: all 0.3s ease;
        }}
        
        .nav-link:hover {{
            color: var(--text-primary);
            background-color: var(--bg-secondary);
            border-left-color: var(--primary-color);
        }}
        
        .nav-link.active {{
            color: var(--text-primary);
            background-color: var(--bg-secondary);
            border-left-color: var(--primary-color);
            font-weight: bold;
        }}
        
        /* Card styling */
        .dash-card {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .dash-card-title {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 12px;
            color: var(--text-primary);
        }}
        
        .dash-card-value {{
            font-size: 24px;
            font-weight: bold;
            color: var(--primary-color);
        }}
        
        .dash-card-subtitle {{
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 8px;
        }}
        
        /* Alert styling */
        .alert-success {{
            background-color: rgba({self._hex_to_rgb(colors['success'])}, 0.1);
            border-left: 4px solid var(--success-color);
            color: var(--success-color);
        }}
        
        .alert-warning {{
            background-color: rgba({self._hex_to_rgb(colors['warning'])}, 0.1);
            border-left: 4px solid var(--warning-color);
            color: var(--warning-color);
        }}
        
        .alert-danger {{
            background-color: rgba({self._hex_to_rgb(colors['danger'])}, 0.1);
            border-left: 4px solid var(--danger-color);
            color: var(--danger-color);
        }}
        
        /* Responsive design */
        @media (max-width: {self.config.mobile_breakpoint}px) {{
            aside {{
                display: none;
            }}
            
            main {{
                width: 100%;
            }}
            
            .dash-card {{
                padding: 12px;
            }}
        }}
        
        /* Loading spinner */
        .spinner {{
            border: 4px solid var(--bg-secondary);
            border-top-color: var(--primary-color);
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 0.8s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        """
        
        # Create a dcc.Stylesheet to inject CSS
        # Store CSS in a hidden div for now (will be injected via callback if needed)
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                ''' + custom_css + '''
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB comma-separated string.
        
        Args:
            hex_color: Color in hex format (e.g., '#FF0000')
            
        Returns:
            RGB format string (e.g., '255, 0, 0')
        """
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))
    
    def register_callbacks(self, callback_registry=None):
        """Register callbacks for interactivity.
        
        Args:
            callback_registry: Optional callback registry object to register callbacks from
        """
        # Callbacks will be registered here in Phase 2b-2c
        # For now, we have a basic placeholder
        pass
    
    def run(self, debug: bool = True, host: str = "127.0.0.1", port: int = 8050) -> None:
        """Run the dashboard server.
        
        Args:
            debug: Enable debug mode (auto-reload, error details)
            host: Host to bind to
            port: Port to run on
        """
        self.app.run_server(debug=debug, host=host, port=port)
    
    def get_app(self):
        """Get the underlying Dash application instance.
        
        Returns:
            The Dash app instance for advanced configuration
        """
        return self.app


def create_app(config: DashboardConfig = None, mock_data: dict = None) -> Dash:
    """Factory function to create a Dash application.
    
    Useful for deployment scenarios where you need to create
    the app as a module-level variable.
    
    Args:
        config: Optional DashboardConfig instance
        mock_data: Optional mock data dictionary for development
        
    Returns:
        Configured Dash application instance
    """
    dashboard = DashboardApp(config=config, mock_data=mock_data)
    return dashboard.app


if __name__ == "__main__":
    # Development entry point
    dashboard = DashboardApp()
    dashboard.run(debug=True)
