"""
Generic form renderer: takes a FormSpec JSON from the API and renders Streamlit widgets.
This module has zero knowledge of workflow logic - it just renders what the API tells it.
"""

import streamlit as st
from datetime import datetime, date, time


def render_form(form_spec: dict) -> tuple[dict | None, str | None]:
    """
    Render Streamlit widgets from a FormSpec dict.

    Returns:
        (field_values, action_key) when an action button is pressed
        (None, None) if no action was taken
    """
    fields = form_spec.get("fields", [])
    actions = form_spec.get("actions", [])

    for field in fields:
        _render_field(field)

    # Show validation errors if any
    if "validation_errors" in st.session_state:
        errors = st.session_state.validation_errors
        for field_name, error_msg in errors.items():
            st.error(f"{field_name}: {error_msg}")
        del st.session_state.validation_errors

    # Render action buttons
    if actions:
        cols = st.columns(len(actions))
        for i, action in enumerate(actions):
            if cols[i].button(action["title"], key=f"action_{action['key']}", use_container_width=True):
                values = _collect_field_values(fields)
                return values, action["key"]

    return None, None


def _render_field(field: dict):
    """Render a single field based on its type."""
    name = field["name"]
    title = field.get("title", name)
    field_type = field.get("type", "text_input")
    value = field.get("value")
    disabled = field.get("disabled", False)
    options = field.get("options")
    validation = field.get("validation")

    help_text = None
    if validation and validation.get("description"):
        help_text = validation["description"]

    if field_type == "checkbox":
        st.checkbox(title, value=bool(value), key=name, disabled=disabled, help=help_text)

    elif field_type == "toggle":
        st.toggle(title, value=bool(value), key=name, disabled=disabled, help=help_text)

    elif field_type == "radio":
        idx = 0
        if options and value in options:
            idx = options.index(value)
        st.radio(title, options=options or [], index=idx, key=name, disabled=disabled, help=help_text)

    elif field_type == "selectbox":
        idx = 0
        if options and value in options:
            idx = options.index(value)
        st.selectbox(title, options=options or [], index=idx, key=name, disabled=disabled, help=help_text)

    elif field_type == "multiselect":
        default = value if isinstance(value, list) else []
        st.multiselect(title, options=options or [], default=default, key=name, disabled=disabled, help=help_text)

    elif field_type == "slider":
        min_val = field.get("min_value", 0.0)
        max_val = field.get("max_value", 100.0)
        step = field.get("step", 1.0)
        val = value if value is not None else min_val
        st.slider(title, min_value=min_val, max_value=max_val, value=val, step=step, key=name, disabled=disabled, help=help_text)

    elif field_type == "select_slider":
        opts = options or []
        st.select_slider(title, options=opts, key=name, disabled=disabled, help=help_text)

    elif field_type == "text_input":
        st.text_input(title, value=str(value) if value else "", key=name, disabled=disabled, help=help_text)

    elif field_type == "number_input":
        val = float(value) if value is not None else 0.0
        st.number_input(title, value=val, key=name, disabled=disabled, help=help_text)

    elif field_type == "text_area":
        st.text_area(title, value=str(value) if value else "", key=name, disabled=disabled, help=help_text)

    elif field_type == "date_input":
        if isinstance(value, str) and value:
            try:
                val = datetime.fromisoformat(value).date()
            except ValueError:
                val = date.today()
        else:
            val = date.today()
        st.date_input(title, value=val, key=name, disabled=disabled, help=help_text)

    elif field_type == "time_input":
        if isinstance(value, str) and value:
            try:
                parts = value.split(":")
                val = time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                val = time(0, 0)
        else:
            val = time(0, 0)
        st.time_input(title, value=val, key=name, disabled=disabled, help=help_text)

    elif field_type == "color_picker":
        st.color_picker(title, value=value or "#ffffff", key=name, disabled=disabled, help=help_text)

    elif field_type == "file_uploader":
        st.file_uploader(title, key=name, disabled=disabled, help=help_text)

    elif field_type == "dataframe":
        if value:
            st.write(title)
            st.dataframe(value)

    else:
        # Fallback to text input for unknown types
        st.text_input(title, value=str(value) if value else "", key=name, disabled=disabled, help=help_text)


def _collect_field_values(fields: list[dict]) -> dict:
    """Collect current widget values from session state."""
    values = {}
    for field in fields:
        name = field["name"]
        if name in st.session_state:
            val = st.session_state[name]
            # Serialize non-JSON types
            if isinstance(val, (date, datetime)):
                val = val.isoformat()
            elif isinstance(val, time):
                val = val.isoformat()
            values[name] = val
    return values


def render_audit_trail(audit_trail: list[dict]):
    """Render audit trail as a table."""
    if not audit_trail:
        st.info("No audit entries yet.")
        return

    import pandas as pd
    df = pd.DataFrame(audit_trail)
    display_cols = [c for c in ["status", "action", "description", "timestamp", "user", "role"] if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True)
