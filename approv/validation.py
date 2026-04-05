import re
import yaml


class ValidationService:
    def __init__(self, validation_config: dict | None = None, config_path: str | None = None):
        if validation_config is not None:
            self.rules = validation_config.get("validations", {})
        elif config_path is not None:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            self.rules = config.get("validations", {})
        else:
            self.rules = {}

    def get_rule(self, rule_name: str) -> dict | None:
        return self.rules.get(rule_name)

    def validate_field(self, field_name: str, value: str, rule_name: str) -> str | None:
        """Returns error message or None if valid."""
        rule = self.rules.get(rule_name)
        if not rule:
            return None
        regex = rule.get("regex")
        if not regex:
            return None
        if not re.match(regex, str(value)):
            return f"Invalid {rule.get('description', field_name)}: {value}"
        return None

    def validate_form(self, form_data: dict, field_rules: dict[str, str]) -> dict[str, str]:
        """
        Validate multiple fields.
        field_rules maps field_name -> validation_rule_name.
        Returns {field_name: error_message} for failures only.
        """
        errors = {}
        for field_name, rule_name in field_rules.items():
            if field_name in form_data and form_data[field_name] is not None:
                err = self.validate_field(field_name, form_data[field_name], rule_name)
                if err:
                    errors[field_name] = err
        return errors
