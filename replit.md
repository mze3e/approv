# Approv - Workflow Management System

## Overview
A business process management system (BPMS) built with Python, Streamlit, and DuckDB. This application provides a workflow engine for managing business processes with user-friendly interfaces.

## Recent Changes
- 2024-09-24: Successfully imported GitHub repository and configured for Replit environment
- Fixed Python dependencies and code issues
- Configured Streamlit for proper hosting on 0.0.0.0:5000
- Set up deployment configuration for autoscale deployment
- Fixed LSP diagnostics in spiffworkflow.py by commenting out deprecated API usage

## Project Architecture
- **Frontend**: Streamlit web application with multi-page interface
- **Database**: DuckDB for lightweight, embedded database functionality
- **Workflow Engine**: Custom workflow management using Python classes
- **Configuration**: YAML-based configuration for workflows and forms

## Key Files
- `🏠_Home.py`: Main Streamlit application entry point
- `approv/`: Core workflow management modules
  - `Form.py`: Form handling and validation
  - `Workflow.py`: Workflow engine logic
  - `WorkflowStep.py`: Individual workflow step management
- `pages/`: Additional Streamlit pages
  - `👺_User_Admin.py`: User and role administration
  - `⚙️_Workflow_Admin.py`: Workflow configuration interface
- `.streamlit/config.toml`: Streamlit configuration for Replit hosting

## Configuration
- **Host**: 0.0.0.0:5000 (configured for Replit proxy)
- **Database**: DuckDB (file-based: bpms.db)
- **Deployment**: Autoscale deployment target configured

## Running the Application
The application runs automatically via the configured workflow. Access it through the Replit preview window.

## Dependencies
All Python dependencies are managed via requirements.txt and are installed automatically.