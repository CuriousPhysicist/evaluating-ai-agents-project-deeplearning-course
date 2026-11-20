---
title: "Phase 2b-2 Kickoff: Frontend Framework Setup"
date: 2026-11-18
layout: default
categories: [phase-2b, frontend, dashboard, dash-plotly]
tags: [dash, plotly, ui-framework, frontend, mobile-first]
status: planning
---

# Phase 2b-2 Kickoff: Frontend Framework Setup

**Phase:** 2b-2 (of 7 planned phases)  
**Date Started:** November 18, 2026  
**Dependency:** ✅ Phase 2b-1 Completed  
**Technology Stack:** Dash (Plotly), Python  
**Design Approach:** Mobile-first, responsive layout  

## Overview

Phase 2b-2 focuses on setting up the Dash/Plotly framework and building the fundamental dashboard structure. This phase establishes:

1. **Dash Application Structure** - Main app file with callbacks
2. **Responsive Layout** - Header, sidebar, main content area
3. **Navigation System** - Routing between dashboard views
4. **Component Templates** - Reusable UI components
5. **Styling & Theming** - Mobile-first CSS and Dash Bootstrap
6. **Configuration System** - Customizable dashboard settings

## Success Criteria

✅ **Code Delivery:**
- Dash app structure created with main application file
- Responsive layout with header, sidebar, main content
- Working routing between at least 2 dashboard views
- Component library with 5+ reusable components
- Mobile-responsive styling implemented
- Configuration system for customization

✅ **Quality Standards:**
- All new code has docstrings
- Code follows PEP 8 style guidelines
- No breaking changes to existing code
- Clear separation of concerns (layout, callbacks, utilities)

✅ **Testing:**
- Layout renders without errors
- Routing works correctly between views
- Components accept correct props
- Configuration system loads and applies settings

✅ **Documentation:**
- README explaining dashboard structure
- Component documentation with examples
- Configuration guide for customization

## Architecture Design

### File Structure

```
agent_evals/dashboard/
├── __init__.py                 # Module initialization
├── query_service.py            # ✅ Phase 2b-1: Query abstraction
├── data_transformer.py         # ✅ Phase 2b-1: Data transformation
├── app.py                      # 🔄 Phase 2b-2: Main Dash application
├── callbacks.py                # 🔄 Phase 2b-2: Callback handlers
├── layout.py                   # 🔄 Phase 2b-2: Main layout structure
├── components/
│   ├── __init__.py
│   ├── header.py               # 🔄 Phase 2b-2: Header component
│   ├── sidebar.py              # 🔄 Phase 2b-2: Sidebar navigation
│   ├── cards.py                # 🔄 Phase 2b-2: Card components
│   ├── charts.py               # 🔄 Phase 2b-2: Chart wrappers
│   └── alerts.py               # 🔄 Phase 2b-2: Alert components
├── views/
│   ├── __init__.py
│   ├── dashboard.py            # 🔄 Phase 2b-2: Main dashboard view
│   ├── trends.py               # ⏳ Phase 2b-3: Trend analysis view
│   ├── requirements.py         # ⏳ Phase 2b-3: Per-requirement view
│   └── comparison.py           # ⏳ Phase 2b-3: Version comparison view
├── config.py                   # 🔄 Phase 2b-2: Configuration system
└── utils.py                    # 🔄 Phase 2b-2: Utility functions

tests/
├── test_dashboard_queries.py   # ✅ Phase 2b-1: Backend tests
├── test_dashboard_layout.py    # 🔄 Phase 2b-2: Layout component tests
└── test_dashboard_callbacks.py # 🔄 Phase 2b-2: Callback logic tests
```

### Main Application Structure

```python
# agent_evals/dashboard/app.py
from dash import Dash, dcc, html, Input, Output
from agent_evals.dashboard.layout import create_layout
from agent_evals.dashboard.callbacks import register_callbacks
from agent_evals.dashboard.query_service import DashboardQueryService
from agent_evals.dashboard.config import DashboardConfig

class DashboardApp:
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
        self.app = Dash(__name__)
        self.query_service = DashboardQueryService()
        
        # Set up layout and callbacks
        self.app.layout = create_layout(self.config)
        register_callbacks(self.app, self.query_service)
    
    def run(self, debug=True, host="127.0.0.1", port=8050):
        """Run the dashboard."""
        self.app.run_server(debug=debug, host=host, port=port)
```

### Layout Structure (Mobile-First)

**Header (Top navigation):**
- Logo/Title
- Project selector dropdown
- Quick stats (current score, trend)
- Mobile hamburger menu

**Sidebar (Collapsible):**
- Navigation links (Dashboard, Trends, Requirements, Comparison)
- Filter controls (date range, version)
- Settings button

**Main Content Area:**
- Current view component
- Responsive grid layout
- Mobile-optimized spacing

**Footer:**
- Last updated timestamp
- Help/documentation links
- Version information

### Component Library

**Dashboard Components to Implement:**

1. **Header Component** (`components/header.py`)
   - Logo and title
   - Project selector
   - Summary stats display
   - Mobile menu toggle

2. **Sidebar Component** (`components/sidebar.py`)
   - Navigation menu
   - Date range picker
   - Version selector
   - Filter controls

3. **Card Component** (`components/cards.py`)
   - Score summary card
   - Metric card
   - Trend indicator card
   - Alert card

4. **Chart Wrappers** (`components/charts.py`)
   - Line chart wrapper
   - Heatmap wrapper
   - Comparison chart wrapper
   - Responsive container

5. **Alert Component** (`components/alerts.py`)
   - Regression alert
   - Improvement alert
   - Info alert
   - Error alert

### Callback System

**Primary Callbacks:**
1. Navigation between views
2. Date range filter
3. Version selector
4. Mobile menu toggle
5. Data refresh trigger

**Data Flow:**
```
User Input (Callback) → Query Service → Data Transformer → Component Update
```

### Configuration System

```python
# agent_evals/dashboard/config.py
from dataclasses import dataclass

@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    app_title: str = "AI Agent Compliance Dashboard"
    theme: str = "light"  # or "dark"
    primary_color: str = "#1f77b4"
    mobile_breakpoint: int = 768  # pixels
    refresh_interval: int = 300  # seconds
    max_data_points: int = 100  # for performance
    enable_dark_mode: bool = True
    enable_export: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
```

## Implementation Plan

### Phase 2b-2a: Core App Setup (1st Priority)
**Deliverables:**
- Dash app initialization
- Main layout structure (header, sidebar, content)
- Basic CSS styling
- Application entry point

**Files to Create:**
- `app.py` - Main application class
- `layout.py` - Layout structure
- `config.py` - Configuration system
- `components/__init__.py`
- `views/__init__.py`

### Phase 2b-2b: Component Library (2nd Priority)
**Deliverables:**
- Header component with responsive design
- Sidebar component with navigation
- Card components for metrics
- Chart wrapper components
- Alert components

**Files to Create:**
- `components/header.py`
- `components/sidebar.py`
- `components/cards.py`
- `components/charts.py`
- `components/alerts.py`

### Phase 2b-2c: Routing & Callbacks (3rd Priority)
**Deliverables:**
- Page routing system
- Navigation callbacks
- Filter callbacks
- Dashboard view (initial view)

**Files to Create:**
- `callbacks.py`
- `views/dashboard.py`
- `utils.py`

### Phase 2b-2d: Testing & Integration (4th Priority)
**Deliverables:**
- Layout tests
- Component tests
- Callback tests
- Integration with query service

**Files to Create:**
- `tests/test_dashboard_layout.py`
- `tests/test_dashboard_callbacks.py`

## Technology Details

### Dash/Plotly Framework

**Why Dash?**
- Pure Python framework (no JavaScript required)
- Built on Plotly for interactive charts
- Reactive callbacks (similar to web frameworks)
- Mobile-responsive components
- Extensive component library
- Good documentation and community

**Key Libraries:**
```python
dash                    # Main framework
plotly                  # Charts and graphics
dash-bootstrap-components  # Responsive CSS framework
pandas                  # Data manipulation (already used)
```

### Mobile-First Approach

**Principles:**
1. Start with mobile layout
2. Use responsive breakpoints
3. Test on actual mobile devices
4. Optimize for touch interactions
5. Minimize data transfer

**Implementation:**
- Use Dash Bootstrap Components for responsive grid
- Mobile-first CSS media queries
- Touch-friendly component sizes
- Responsive charts via Plotly

### Styling Strategy

**Color Scheme:**
- Primary: Blue (#1f77b4) - main actions
- Success: Green (#2ca02c) - improvements
- Warning: Orange (#ff7f0e) - cautions
- Danger: Red (#d62728) - regressions
- Neutral: Gray (#7f7f7f) - secondary

**Layout Spacing:**
- Mobile: 8px base unit
- Tablet: 12px base unit
- Desktop: 16px base unit

**Typography:**
- Headers: Roboto Bold
- Body: Roboto Regular
- Monospace: Courier New (for data)

## Development Workflow

### Step 1: Create App Structure
```bash
# Create app.py with Dash application class
# Create layout.py with main layout structure
# Create config.py with configuration system
```

### Step 2: Build Components
```bash
# Create components/__init__.py
# Implement header.py
# Implement sidebar.py
# Implement cards.py and charts.py
```

### Step 3: Implement Routing
```bash
# Create views/__init__.py
# Create views/dashboard.py
# Implement basic dashboard view
# Set up navigation routing
```

### Step 4: Add Callbacks
```bash
# Create callbacks.py
# Implement navigation callbacks
# Implement filter callbacks
# Test interactions
```

### Step 5: Add Tests
```bash
# Create test_dashboard_layout.py
# Create test_dashboard_callbacks.py
# Write layout tests
# Write callback tests
```

## Expected Challenges & Solutions

| Challenge | Expected | Solution |
|-----------|----------|----------|
| Responsive layout complexity | High | Use Dash Bootstrap Components, start simple |
| Callback debugging | Medium | Use print statements, Dash DevTools |
| Mobile testing | Medium | Test in browser DevTools, actual devices |
| Performance with large data | Low for MVP | Mock data is small; optimize in Phase 2b-3 |
| Styling consistency | Medium | Use configuration system, CSS modules |

## Validation Criteria

### Code Quality
- [ ] No linting errors (Pylint, Flake8)
- [ ] All functions have docstrings
- [ ] Code follows PEP 8
- [ ] No hardcoded values (use config)

### Functionality
- [ ] Dashboard loads without errors
- [ ] All views render correctly
- [ ] Navigation works between views
- [ ] Responsive on mobile, tablet, desktop
- [ ] Dark mode works (if implemented)

### Integration
- [ ] Query service integration works
- [ ] Data flows correctly through transformer
- [ ] Components receive correct data
- [ ] Charts render from transformed data

### Testing
- [ ] Layout component tests pass
- [ ] Callback logic tests pass
- [ ] Integration tests pass
- [ ] Manual testing on mobile completed

## Resources & References

**Dash Documentation:**
- https://dash.plotly.com/
- https://dash-bootstrap-components.opensource.faculty.ai/

**Plotly Charts:**
- https://plotly.com/python/

**Mobile-First Design:**
- Mobile-first CSS approach
- Responsive breakpoints
- Touch-friendly UI

## Deliverables Summary

**Files to Create:** 10+
**New Code:** ~2,000-2,500 lines
**Tests:** 20+
**Documentation:** 2-3 files

**Timeline Estimate:** 2-3 development sessions
- Session 1: App structure + components (Phase 2b-2a & 2b-2b)
- Session 2: Routing + callbacks (Phase 2b-2c)
- Session 3: Testing + refinement (Phase 2b-2d)

## Next Steps

1. ✅ Reviewed Phase 2b-1 completion
2. ⏳ Ready to begin Phase 2b-2a (Core App Setup)
3. 📋 Use this kickoff document as development guide
4. 📝 Update documentation as implementation progresses

---

**Previous Phase:** ✅ [Phase 2b-1: Backend Data Service](./PHASE_2b_PART_1_COMPLETION.md)  
**Next Phase:** ⏳ Phase 2b-3: Dashboard Views & Integration  

*This is the second phase of Phase 2b (Interactive Dashboard). The dashboard will provide real-time compliance score visualization with mobile-first responsive design.*
