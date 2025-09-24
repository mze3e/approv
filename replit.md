# Approv - Workflow Management System

## Overview
A business process management system (BPMS) built with Python, Streamlit, and DuckDB. This application provides a workflow engine for managing business processes with user-friendly interfaces.

## Recent Changes
- 2024-09-24: **PHASE 2 COMPLETE**: Successfully migrated core Streamlit components to Shiny Python
- Implemented dynamic form rendering with 16 widget types (checkbox, radio, selectbox, slider, text inputs, file uploads, etc.)
- Created reactive workflow processing with non-blocking continuation using reactive.invalidate_later
- Added role-based field permissions with CSS enforcement and server-side validation
- Implemented action button handling and form submission via ShinyFormRenderer.setup_action_handlers
- Added real-time audit trail tracking and DataFrame display
- Fixed state synchronization between reactive values and workflow instance data
- Configured app for proper hosting on 0.0.0.0:5000 with Shiny Python server
- All critical integration issues resolved - production-ready BPMS with full workflow progression

## Project Architecture
- **Frontend**: Shiny Python web application with reactive multi-page interface
- **Database**: DuckDB for lightweight, embedded database functionality  
- **Workflow Engine**: Reactive workflow management using Shiny Python classes with dynamic form rendering
- **Configuration**: YAML-based configuration for workflows and forms
- **Core Modules**:
  - `shiny_modules/form.py`: Dynamic form rendering with 16 widget types and role-based permissions
  - `shiny_modules/workflow.py`: Reactive workflow processing with non-blocking continuation
  - `shiny_modules/config.py`: Configuration management and secure database integration

## Key Files
- `app.py`: Main Shiny Python application with reactive server logic
- `shiny_modules/`: Core Shiny workflow management modules
  - `form.py`: Dynamic form rendering with 16 widget types and role-based permissions
  - `workflow.py`: Reactive workflow processing with non-blocking continuation  
  - `config.py`: Configuration management and secure database integration
- `approv/`: Original Streamlit modules (preserved for reference)
- `form.yaml`: Form configuration with widget types and permissions
- `workflow.yaml`: Workflow step definitions and transitions
- `data.json`: Initial form data and user configurations

## Configuration
- **Host**: 0.0.0.0:5000 (configured for Replit proxy with Shiny Python server)
- **Database**: DuckDB (file-based: bpms.db) with read-only SQL protection
- **Deployment**: Autoscale deployment target configured for production
- **Reactive Features**: Non-blocking workflow continuation, real-time audit trail, dynamic form rendering

## Running the Application
The Shiny Python application runs automatically via the configured workflow. Features include:
- **Dynamic Form Rendering**: 16 widget types with real-time role-based permissions
- **Reactive Workflow Processing**: Non-blocking progression through workflow steps
- **Multi-User Support**: Role switching between GENERAL_USER and PRESIDENT_USER
- **Real-Time Audit Trail**: Live tracking of workflow actions and status changes
- **Database Administration**: Secure read-only SQL query interface

Access the application through the Replit preview window to experience the modernized BPMS interface.

## Dependencies
All Python dependencies are managed via requirements.txt and are installed automatically.