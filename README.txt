Estelar Revenue Dashboard
=========================

Overview
--------
This project is a Streamlit revenue analytics application for airline ticket-system data.
It is designed to work primarily from PostgreSQL views populated from airline sales CSV
files and normalized coupon-level data.

The application supports:
- Executive dashboard metrics
- Revenue by emisor
- Tariff-style analysis
- Yield by route
- Volado analysis
- Programmed revenue by flight
- Route analysis
- Purchase vs programmed heatmap
- Sales reporting
- Sales by user
- Admin catalog maintenance
- CSV data load workflow

Run locally on Mac
------------------
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

Environment
-----------
The app expects a .env file in the project root with:

DATABASE_URL=postgresql+psycopg2://...

Main execution flow
-------------------
The application follows this flow:

1. app.py
   - configures Streamlit
   - applies global styles
   - validates database connection
   - builds shared app context
   - resolves the selected module runner

2. core/navigation.py
   - defines the sidebar module labels
   - renders the sidebar module selector

3. core/module_registry.py
   - maps each visible module label to a router runner function

4. core/module_router.py
   - loads shared data when needed
   - calls service-layer preparation functions
   - calls UI render functions

5. services/
   - prepares module-specific data for views
   - orchestrates report builders and helper logic
   - contains special preparation paths for modules like Programmed Revenue and Volado

6. ui/
   - renders Streamlit pages and controls
   - handles exports, filters, formatted tables, and module layouts

7. reports/
   - contains report builders and aggregation logic
   - transforms dataframes into the tables used by modules

8. charts/
   - contains Plotly and PNG chart builders for app screens and PDF exports

9. exporters/
   - contains Excel and PDF output helpers

10. db_data_loader.py / db_loader.py / load_service.py
    - database reads
    - CSV normalization and ingestion
    - data load preview and execution

Project structure
-----------------
Recommended mental model:

- app.py
- core/
  - navigation.py
  - module_registry.py
  - module_router.py
  - branding.py
  - layout.py
  - styles.py
- services/
- ui/
- reports/
- charts/
- exporters/
- db_data_loader.py
- db_loader.py
- load_service.py
- config.py
- requirements.txt

Layer responsibilities
----------------------
core/
- App shell only
- Navigation, layout, branding, registry, module dispatch

services/
- Module preparation only
- No Streamlit page rendering here
- Can call reports and shared helpers

ui/
- Streamlit rendering only
- User controls, tables, charts, export buttons
- Should avoid heavy business aggregation logic

reports/
- Business/report logic
- Pandas grouping, transformations, report tables

charts/
- Chart creation only
- Plotly for interactive views
- PNG helpers for PDFs

exporters/
- Excel and PDF generation only

db/
- Database reads and CSV ingestion workflow

Important design note
---------------------
Programmed Revenue and Volado intentionally use specialized preparation paths.
They do not have to follow the exact same internal flow as the standard modules.
That is expected and should be preserved unless there is a clear business reason
to redesign them.

How to add a new module
-----------------------
1. Create or update the report builder in reports/ if needed
2. Create a service-layer prepare function in services/
3. Create a render function in ui/
4. Add the runner in core/module_router.py
5. Register the module in core/module_registry.py
6. Add the visible label in core/navigation.py
7. Test the module from the Streamlit sidebar

How to modify an existing module
--------------------------------
If the change is about:
- data aggregation -> start in reports/
- module payload preparation -> start in services/
- screen layout or controls -> start in ui/
- app navigation or dispatch -> start in core/
- export formatting -> start in exporters/
- database query/filtering -> start in db_data_loader.py

Current data source model
-------------------------
The standard analytic modules depend on database-backed data loaded through
db_data_loader.py.

Typical returned objects include:
- df: ticket-level or raw-level analytic frame
- coupons_long: coupon-level analytic frame
- kpis: KPI dictionary for shell cards
- routes: route options for route-based modules

The data-load flow is separate and supports:
- CSV preview
- load execution
- load history

Maintenance rules
-----------------
To keep the project manageable:

1. Do not put Streamlit rendering inside services/
2. Do not put business aggregation inside ui/ unless it is truly display-only
3. Keep module labels aligned between:
   - navigation.py
   - module_registry.py
4. Prefer one clear prepare entry and one clear render entry per module
5. Reuse shared UI helpers instead of duplicating styles or filter controls
6. Keep Programmed Revenue and Volado special handling explicit and documented

Safe refactor strategy
----------------------
When refactoring:
- prefer small, reversible changes
- avoid changing business rules and organization in the same step
- test Dashboard, Sales, Programmed Revenue by Flight, Volado, Route Analysis,
  and Data Load after each cleanup step

Notes
-----
This project is already modular.
Future improvements should focus on:
- readability
- reducing duplication
- documenting responsibilities
- keeping public entry points clear