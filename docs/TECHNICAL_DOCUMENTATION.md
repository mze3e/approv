# ApproV Technical Documentation

## 1. Overview
ApproV is an open-source workflow engine implemented in Python with Streamlit-based user interfaces and DuckDB-backed utilities, designed to orchestrate human-driven approval flows defined through YAML configuration files.【F:README.md†L1-L2】【F:🏠_Home.py†L1-L31】

## 2. High-Level Architecture
The solution is organized into the following layers:

| Layer | Key Components | Responsibilities |
| --- | --- | --- |
| Presentation | `🏠_Home.py`, `pages/⚙️_Workflow_Admin.py`, `pages/👺_User_Admin.py` | Streamlit apps that collect user input, visualize workflow state, and expose administrative tooling.【F:🏠_Home.py†L1-L31】【F:pages/⚙️_Workflow_Admin.py†L1-L75】【F:pages/👺_User_Admin.py†L1-L135】 |
| Workflow Engine | `approv/Workflow.py`, `approv/WorkflowStep.py` | Core execution loop that interprets workflow definitions, enforces permissions, and progresses the state machine.【F:approv/Workflow.py†L9-L135】【F:approv/WorkflowStep.py†L1-L63】 |
| Form Runtime | `approv/Form.py`, `form.yaml`, `data.json` | Dynamically renders form fields and actions defined in YAML, initializes defaults, and collects submitted values.【F:approv/Form.py†L9-L265】【F:form.yaml†L1-L33】【F:data.json†L1-L18】 |
| Configuration | `workflow.yaml`, `users_and_roles.yaml`, `type_validation.yaml` | Declarative definitions for workflow steps, access permissions, and validation rules.【F:workflow.yaml†L1-L106】【F:users_and_roles.yaml†L1-L69】【F:type_validation.yaml†L1-L104】 |
| Utilities & Samples | `utils.py`, `spiffworkflow.py`, validation scripts | Shared helpers and illustrative code for extending the engine or integrating external libraries.【F:utils.py†L1-L29】【F:spiffworkflow.py†L1-L35】【F:validation.py†L1-L43】 |

## 3. Streamlit Presentation Layer
- **Home application (`🏠_Home.py`)** initializes workflow and form configurations from YAML, loads persisted form data, and exposes a user role selector that determines available actions.【F:🏠_Home.py†L8-L31】 When the user starts the workflow, the Streamlit session delegates processing to the engine and renders the dynamic form bound to the current state.【F:🏠_Home.py†L26-L31】
- **Workflow admin page** surfaces the YAML-defined workflow graph in tabular and graph formats, providing quick inspection and inline editing of node metadata before persisting changes manually.【F:pages/⚙️_Workflow_Admin.py†L10-L75】 It uses `streamlit-agraph` to visualize status transitions and annotate conditional edges.【F:pages/⚙️_Workflow_Admin.py†L31-L53】
- **User admin page** connects to a DuckDB database, executes ad-hoc SQL through a text box, and exposes CRUD-style forms scaffolded for managing users, roles, and permissions (persisting is left as an exercise).【F:pages/👺_User_Admin.py†L15-L135】

## 4. Workflow Engine
### 4.1 Workflow Orchestration
The `Workflow` class maintains the active status, audit trail, and associated form, seeding initial state from the YAML configuration and any stored form data.【F:approv/Workflow.py†L9-L29】 It exposes lifecycle helpers (`initiate`, `cancel`) that update status and append audit entries.【F:approv/Workflow.py†L32-L40】 Each audit entry captures the status, action, description, timestamp, and user responsible.【F:approv/Workflow.py†L27-L29】

### 4.2 Execution Loop
`process_workflow` enforces comment logging, then repeatedly pulls the current step definition, checks role permissions, instantiates the step class, and records the resulting status transition until user interaction is again required or the workflow ends.【F:approv/Workflow.py†L81-L110】 Permission checks compare the acting user's role to the step's allowed roles, raising if the action is not authorized.【F:approv/Workflow.py†L91-L115】 The method also maintains the persisted status field inside the form payload to keep UI and engine views synchronized.【F:approv/Workflow.py†L95-L110】

### 4.3 Step Implementations
Step behaviors are defined in `approv/WorkflowStep.py`. Simple linear steps hand back their configured next status, a REST call stub simulates integration success, and a stop step ends execution.【F:approv/WorkflowStep.py†L1-L40】 The `ExclusiveChoice` implementation iterates over configured conditions and currently supports equality checks, defaulting to the fallback path when no conditions match.【F:approv/WorkflowStep.py†L42-L63】

## 5. Dynamic Form Rendering
The `Form` class loads field, action, and permission metadata from YAML, allowing either in-memory dictionaries or file paths to be supplied.【F:approv/Form.py†L21-L50】 `_default_value` and `_is_disabled` derive default field values and editability constraints based on field types and user roles.【F:approv/Form.py†L52-L96】 `get_form` walks the configured fields to render the appropriate Streamlit widgets, converts persisted values to widget-friendly formats, and renders action buttons tied to workflow actions.【F:approv/Form.py†L98-L245】 Submitted data is collected via `get_form_data`, which consolidates widget state and records the last action pressed so the workflow can react accordingly.【F:approv/Form.py†L247-L265】

## 6. Configuration Files
- **Workflow definition (`workflow.yaml`)** describes a state machine with start, decision, service, and stop nodes, including conditional routing rules and whether user input is required at each step.【F:workflow.yaml†L1-L93】 Comments capture the catalog of supported step and condition types for future expansion.【F:workflow.yaml†L94-L106】
- **Form definition (`form.yaml`)** outlines visible fields, available actions, and role-based field permissions used by the dynamic form renderer.【F:form.yaml†L1-L33】
- **Seed data (`data.json`)** provides initial values for form inputs, ensuring the UI can hydrate session state before the first user interaction.【F:data.json†L1-L18】
- **Users and roles (`users_and_roles.yaml`)** enumerate sample personnel, their contact information, and permission bundles associated with each role.【F:users_and_roles.yaml†L1-L69】
- **Validation rules (`type_validation.yaml`)** centralize reusable regular-expression checks for common data quality requirements that can be referenced from form field definitions.【F:type_validation.yaml†L1-L104】

## 7. Validation Utilities
Two scripts (`validation.py` and `approv/Validation.py`) demonstrate how to load the shared validation catalog and apply regex-driven checks to data dictionaries, reporting errors when values fail their associated patterns.【F:validation.py†L1-L43】【F:approv/Validation.py†L1-L43】 These exemplars can be adapted for integrating server-side validation into workflow steps or form submissions.

## 8. Supporting Utilities and Samples
- `utils.py` contains helper functions for string alignment and numeric rounding used by form rendering logic.【F:utils.py†L1-L29】
- `spiffworkflow.py` showcases how an equivalent nuclear strike workflow can be authored using the external SpiffWorkflow library, providing a reference for alternative execution engines.【F:spiffworkflow.py†L1-L35】

## 9. Execution Sequence
1. A user launches the Streamlit app and selects a role, which seeds the workflow runner and form session state from YAML and JSON files.【F:🏠_Home.py†L8-L31】
2. Upon submitting an action button, the form gathers widget state, records the triggering action, and invokes the workflow engine.【F:approv/Form.py†L238-L265】
3. The engine evaluates the current step, logs audit information, enforces permissions, and updates the workflow status and form payload before returning control to the UI.【F:approv/Workflow.py†L81-L135】
4. If additional automated steps remain, the loop continues until a human decision or the stop state is reached; the updated audit history becomes available to the UI via the form renderer.【F:approv/Workflow.py†L88-L110】【F:approv/Form.py†L93-L118】

## 10. Extending the System
- **Adding workflow steps:** extend `approv/WorkflowStep.py` with new classes (e.g., email notifications), then reference them in `workflow.yaml`. Ensure `process_workflow` can instantiate the new class by exporting it in the module scope.【F:approv/Workflow.py†L94-L99】【F:approv/WorkflowStep.py†L1-L63】
- **Enhancing decisions:** broaden `ExclusiveChoice.process` to support additional operators or complex expressions, and include matching metadata in the YAML definitions.【F:approv/WorkflowStep.py†L42-L63】【F:workflow.yaml†L23-L59】
- **Custom validations:** reference entries in `type_validation.yaml` from form field definitions or invoke the validation scripts during workflow execution to enforce business rules.【F:type_validation.yaml†L1-L104】【F:validation.py†L1-L43】
- **Persisting admin changes:** wire the admin pages to write updates back to YAML or DuckDB tables once edits are submitted, leveraging the placeholder forms already scaffolded.【F:pages/⚙️_Workflow_Admin.py†L55-L75】【F:pages/👺_User_Admin.py†L69-L135】

## 11. Running Locally
1. Install dependencies from `requirements.txt` in a virtual environment (`pip install -r requirements.txt`).【F:requirements.txt†L1-L3】
2. Launch the Streamlit application with `streamlit run 🏠_Home.py` to access the main workflow UI and additional pages in the sidebar.【F:🏠_Home.py†L1-L31】
3. (Optional) Initialize a DuckDB database (`bpms.db`) with `users`, `roles`, and `permissions` tables to power the administrative dashboards showcased in the multipage app.【F:pages/👺_User_Admin.py†L15-L67】

## 12. Known Limitations and Considerations
- `ExclusiveChoice` currently supports only equality comparisons; more complex branching requires code extensions.【F:approv/WorkflowStep.py†L49-L63】
- The `Workflow` permission check expects role names in step definitions; user-level overrides are not yet implemented.【F:approv/Workflow.py†L91-L115】
- Admin forms modify in-memory structures but do not persist updates back to YAML or the database, so changes are ephemeral until persistence logic is added.【F:pages/⚙️_Workflow_Admin.py†L55-L75】【F:pages/👺_User_Admin.py†L69-L135】
- The `Form` renderer assumes all fields declared in YAML exist in the session state; missing data falls back to inferred defaults, which may need tightening for strict validation scenarios.【F:approv/Form.py†L98-L157】

