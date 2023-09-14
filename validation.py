import yaml
import re

# Load the YAML configuration file
with open('type_validation.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

data = {
    "required_field": "Sample Data",
    "length_validation": "12345",
    "numeric_validation": "12345",
    "email_validation": "user^.com",
    "phone_number_validation": "123-456-7890",
    "date_validation": "09/14/2023",
    "password_validation": "P@ssw0rd",
    "username_validation": "user_123",
    "url_validation": "https://www.example.com",
    "dropdown_selection_validation": "Option 1",
    "radio_checkbox_validation": "Option 2",
    "file_upload_validation": "example.txt",
    "captcha_validation": "CaptchaResponse123",
    "unique_field_validation": "UniqueValue123",
    "consistency_validation": "SampleData",
    "credit_card_validation": "1234567890123456",
    "postal_code_validation": "12345",
    "custom_validation": "CustomValidData",
    "cross_field_validation": "CrossFieldValidData",
    "server_side_validation": "ServerSideValidData",
    "sanitization": "<script>alert('Hello');</script>",
    "regex_validation": "RegexValidData123",
    "geographical_validation": "ValidLocation",
    "language_character_set_validation": "ValidCharsetData",
    "accessibility_validation": "AccessibleData",
    "date_time_format_validation": "09/14/2023 10:30 AM"
}

def validate_data(data, config):
    errors = {}
    for field, value in data.items():
        if field not in config['validations']:
            continue  # Skip fields without validation rules

        validation_rule = config['validations'][field]
        regex_pattern = validation_rule.get('regex')
        description = validation_rule.get('description')

        if regex_pattern:
            # Validate the field using the regex pattern
            if not re.match(regex_pattern, value):
                errors[field] = f"Invalid {description}: {value}"

    return errors

# Validate the data
validation_errors = validate_data(data, config)

# Print validation results
if validation_errors:
    print("Validation Errors:")
    for field, error in validation_errors.items():
        print(f"{field}: {error}")
else:
    print("Data is valid.")
