# Approv - Workflow Management System

## Overview
A business process management system (BPMS) built with Python, Streamlit, and DuckDB. This application provides a workflow engine for managing business processes with user-friendly interfaces.

## Recent Changes
- 2024-09-24: **PHASE 3 COMPLETE**: Successfully implemented comprehensive, production-ready Workflow Admin
- **✅ Enterprise-Grade Workflow Administration**:
  - Complete CRUD operations for workflow nodes with validation and integrity enforcement
  - Validation-gated save with atomic transactional writes and rollback protection
  - Complete runtime reload with workflow reconstruction and handler rebinding
  - Reference-safe deletion with blocking behavior and actionable error messages
  - Deep copy safety throughout all operations to prevent state bleed-through
  - Comprehensive validation including Start/Stop constraints, reachability, and consistency checks
- **✅ Production Safety Features**:
  - All operations protected by validation gates that block on integrity errors
  - Atomic workflow instance swapping with rollback on failure
  - Enterprise-grade error handling with clear user feedback
  - Type safety with proper integer coercion for node IDs
  - Reference integrity management across inputs, outputs, and conditions
- **Previous Achievements**: Dynamic form rendering with 16 widget types, reactive workflow processing, role-based permissions, real-time audit trail, multi-page navigation, comprehensive admin interfaces

## Project Architecture
- **Frontend**: Shiny Python web application with reactive multi-page interface
- **Database**: DuckDB for lightweight, embedded database functionality  
- **Workflow Engine**: Reactive workflow management using Shiny Python classes with dynamic form rendering
- **Configuration**: YAML-based configuration for workflows and forms
- **Admin Interface**: Production-ready workflow configuration management with enterprise safety
- **Core Modules**:
  - `shiny_modules/form.py`: Dynamic form rendering with 16 widget types and role-based permissions
  - `shiny_modules/workflow.py`: Reactive workflow processing with non-blocking continuation
  - `shiny_modules/config.py`: Configuration management and secure database integration
  - **Workflow Admin** (in `app.py`): Complete CRUD operations with validation gates, atomic operations, reference safety

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