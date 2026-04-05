"""
Form specification builder.

Produces a FormSpec JSON structure from YAML config, form data, and user roles.
Zero Streamlit imports - this is a pure data transformation.
"""

import yaml
from datetime import date, datetime, time

from approv.models import FormFieldSpec, FormSpec
from approv.validation import ValidationService


class FormSpecBuilder:
    def __init__(
        self,
        form_config: dict,
        validation_service: ValidationService | None = None,
    ):
        if isinstance(form_config, str):
            with open(form_config, "r") as f:
                form_config = yaml.safe_load(f)

        self.form_fields = form_config.get("form", {}).get("fields", {})
        self.actions = form_config.get("form", {}).get("actions", {})
        self.permissions = form_config.get("form", {}).get("permissions", {})
        self.validation_service = validation_service

    def build_spec(
        self,
        form_data: dict,
        user_roles: list[str],
        current_status: str,
        instance_id: int,
    ) -> FormSpec:
        fields = []
        for field_name, field_config in self.form_fields.items():
            field_spec = self._build_field_spec(field_name, field_config, form_data, user_roles)
            fields.append(field_spec)

        actions = self._build_actions(current_status)

        return FormSpec(
            instance_id=instance_id,
            status=current_status,
            fields=fields,
            actions=actions,
        )

    def _build_field_spec(
        self,
        field_name: str,
        field_config: dict,
        form_data: dict,
        user_roles: list[str],
    ) -> FormFieldSpec:
        field_type = field_config.get("type", "text_input")
        disabled = self._is_disabled(field_name, field_config, user_roles)
        value = self._resolve_value(field_name, field_config, form_data)
        validation = self._get_validation(field_config)

        return FormFieldSpec(
            name=field_name,
            title=field_config.get("title", field_name),
            type=field_type,
            value=value,
            disabled=disabled,
            options=field_config.get("options"),
            min_value=field_config.get("min_value"),
            max_value=field_config.get("max_value"),
            step=field_config.get("step"),
            default=field_config.get("default"),
            validation=validation,
        )

    def _is_disabled(self, field_name: str, field_config: dict, user_roles: list[str]) -> bool:
        # Non-editable fields are always disabled
        if field_config.get("editable") is False:
            return True

        # Check role-based permissions
        allowed_roles = self.permissions.get(field_name)
        if allowed_roles:
            if not any(role in allowed_roles for role in user_roles):
                return True

        return False

    def _resolve_value(self, field_name: str, field_config: dict, form_data: dict):
        """Get current value from form_data, or fall back to default."""
        if field_name in form_data and form_data[field_name] is not None and form_data[field_name] != "":
            value = form_data[field_name]
            # Serialize date/time objects for JSON transport
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            if isinstance(value, time):
                return value.isoformat()
            return value

        return self._default_value(field_config)

    def _default_value(self, field_config: dict):
        """Return type-appropriate default value."""
        if "default" in field_config:
            return field_config["default"]

        field_type = field_config.get("type", "text_input")
        if field_type in ("checkbox", "toggle"):
            return False
        elif field_type in ("radio", "selectbox"):
            options = field_config.get("options", [])
            return options[0] if options else None
        elif field_type == "slider":
            return field_config.get("min_value", 0)
        elif field_type == "multiselect":
            return []
        elif field_type == "number_input":
            return 0.0
        elif field_type == "date_input":
            return date.today().isoformat()
        elif field_type == "time_input":
            return "00:00"
        elif field_type == "color_picker":
            return "#ffffff"
        elif field_type == "dataframe":
            return None
        else:
            return ""

    def _get_validation(self, field_config: dict) -> dict[str, str] | None:
        """Look up validation rule for field if configured."""
        rule_name = field_config.get("validate")
        if not rule_name or not self.validation_service:
            return None
        rule = self.validation_service.get_rule(rule_name)
        if rule:
            return {"regex": rule.get("regex", ""), "description": rule.get("description", "")}
        return None

    def _build_actions(self, current_status: str) -> list[dict[str, str]]:
        """Build list of available actions based on current status."""
        if current_status in ("start", "stop"):
            return []
        return [
            {"key": action_name, "title": action_config.get("title", action_name)}
            for action_name, action_config in self.actions.items()
        ]

    def get_field_validation_rules(self) -> dict[str, str]:
        """Extract field_name -> validation_rule_name mapping for server-side validation."""
        rules = {}
        for field_name, field_config in self.form_fields.items():
            rule_name = field_config.get("validate")
            if rule_name:
                rules[field_name] = rule_name
        return rules
