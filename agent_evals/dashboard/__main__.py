#!/usr/bin/env python
"""
Dashboard server entry point.

Runs the interactive compliance dashboard. Can be invoked as:
    python -m agent_evals.dashboard
    
Or configured via environment variables for deployment.
"""

import logging
import sys
from pathlib import Path

from agent_evals.dashboard.app import DashboardApp
from agent_evals.dashboard.config import DashboardConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the dashboard server."""
    try:
        # Load configuration from environment
        config = DashboardConfig.from_env()
        logger.info(f"Dashboard configuration loaded (theme: {config.theme})")
        
        # Create dashboard app
        # In production, you would load real data from Phoenix
        # For now, using mock data for development
        mock_data = get_mock_data()
        
        dashboard = DashboardApp(config=config, mock_data=mock_data)
        logger.info(f"Dashboard initialized: {config.app_title}")
        
        # Run the server
        logger.info("Starting dashboard server...")
        logger.info("Open http://127.0.0.1:8050 in your browser")
        dashboard.run(debug=True, host="127.0.0.1", port=8050)
        
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}", exc_info=True)
        sys.exit(1)


def get_mock_data():
    """Get mock data for development.
    
    Returns:
        Dictionary of mock compliance score data
    """
    return {
        "v1.0.0_main_a1b2c3d_20261115T120000Z": {
            "overall_score": 0.90,
            "per_requirement_scores": {"T1": 0.95, "T2": 0.85, "T3": 0.90},
            "per_requirement_details": {},
            "git_branch": "main",
            "git_commit": "a1b2c3d",
            "project_version": "1.0.0",
            "timestamp": "2026-11-15T12:00:00Z",
            "environment": "development"
        },
        "v1.0.0_main_b2c3d4e_20261116T120000Z": {
            "overall_score": 0.92,
            "per_requirement_scores": {"T1": 0.96, "T2": 0.87, "T3": 0.92},
            "per_requirement_details": {},
            "git_branch": "main",
            "git_commit": "b2c3d4e",
            "project_version": "1.0.0",
            "timestamp": "2026-11-16T12:00:00Z",
            "environment": "development"
        },
        "v1.0.1_feat_c3d4e5f_20261117T120000Z": {
            "overall_score": 0.85,
            "per_requirement_scores": {"T1": 0.90, "T2": 0.80, "T3": 0.85},
            "per_requirement_details": {},
            "git_branch": "feat/optimization",
            "git_commit": "c3d4e5f",
            "project_version": "1.0.1",
            "timestamp": "2026-11-17T12:00:00Z",
            "environment": "development"
        },
    }


if __name__ == "__main__":
    main()
