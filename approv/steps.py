"""
Workflow step implementations.

Each step class follows the contract:
    __init__(self, config: dict)
    process(self, form_data: dict) -> tuple[str | None, str]
        Returns (next_status, description)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def evaluate_condition(operator: str, attribute_value, condition_value) -> bool:
    """Evaluate a condition based on the given operator."""
    if operator == "Equal":
        return attribute_value == condition_value
    elif operator == "GreaterThan":
        return attribute_value > condition_value
    elif operator == "LessThan":
        return attribute_value < condition_value
    elif operator == "GreaterThanOrEqual":
        return attribute_value >= condition_value
    elif operator == "LessThanOrEqual":
        return attribute_value <= condition_value
    elif operator == "Contains":
        return condition_value in attribute_value
    elif operator == "InList":
        return attribute_value in condition_value
    return False


class Start:
    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        return self.config["outputs"][0], "Started"


class Stop:
    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[None, str]:
        return None, "Workflow stopped"


class Simple:
    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        return self.config["outputs"][0], "Simple step executed"


class ExclusiveChoice:
    """If/else branching: evaluates conditions in order, first match wins."""

    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        for condition_name, condition in self.config["conditions"].items():
            if condition_name == "default":
                continue
            operator = condition["operator"]
            attribute = condition["attribute"]
            value = condition["value"]
            if evaluate_condition(operator, form_data.get(attribute), value):
                return condition["next_status"], f"Decision made: {condition_name}"
        return self.config["conditions"]["default"], "Decision made: default"


class MultiChoice:
    """All conditions must be satisfied to proceed to the matching output."""

    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        for output_name, output_config in self.config.get("condition_groups", {}).items():
            conditions = output_config.get("conditions", [])
            if all(
                evaluate_condition(c["operator"], form_data.get(c["attribute"]), c["value"])
                for c in conditions
            ):
                return output_config["next_status"], f"All conditions met: {output_name}"
        return self.config.get("default_output", self.config["outputs"][0]), "MultiChoice: default"


class MutexChoice:
    """At least one condition must be satisfied to proceed."""

    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        for output_name, output_config in self.config.get("condition_groups", {}).items():
            conditions = output_config.get("conditions", [])
            if any(
                evaluate_condition(c["operator"], form_data.get(c["attribute"]), c["value"])
                for c in conditions
            ):
                return output_config["next_status"], f"At least one condition met: {output_name}"
        return self.config.get("default_output", self.config["outputs"][0]), "MutexChoice: default"


class RESTCall:
    """Execute an HTTP request. Config supports url, method, headers, body_template, response_field, error_output."""

    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        import httpx

        url = self.config.get("url", "")
        method = self.config.get("method", "GET").upper()
        headers = self.config.get("headers", {})

        if not url:
            # No URL configured - simulate success (backward compat with mock)
            return self.config["outputs"][0], "RESTCall executed (no URL configured)"

        try:
            url = url.format(**form_data)
        except KeyError:
            pass

        body_template = self.config.get("body_template", {})
        body = {}
        for k, v in body_template.items():
            if isinstance(v, str):
                try:
                    body[k] = v.format(**form_data)
                except KeyError:
                    body[k] = v
            else:
                body[k] = v

        try:
            response = httpx.request(method, url, json=body if body else None, headers=headers, timeout=30)
            response.raise_for_status()
            if "response_field" in self.config:
                form_data[self.config["response_field"]] = response.json()
            return self.config["outputs"][0], f"RESTCall {method} {url} returned {response.status_code}"
        except Exception as e:
            logger.error(f"RESTCall failed: {e}")
            if "error_output" in self.config:
                return self.config["error_output"], f"RESTCall failed: {e}"
            return self.config["outputs"][0], f"RESTCall failed (continuing): {e}"


class EmailNotify:
    """Send email notification. Config: to_field, subject_template, body_template, smtp_*."""

    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        import smtplib
        from email.mime.text import MIMEText
        import os

        to_field = self.config.get("to_field", "email")
        recipient = form_data.get(to_field, "")
        subject = self.config.get("subject_template", "Workflow Notification")
        body = self.config.get("body_template", "You have a workflow update.")

        try:
            subject = subject.format(**form_data)
            body = body.format(**form_data)
        except KeyError:
            pass

        smtp_host = self.config.get("smtp_host", os.environ.get("SMTP_HOST", "localhost"))
        smtp_port = int(self.config.get("smtp_port", os.environ.get("SMTP_PORT", "587")))
        smtp_user = self.config.get("smtp_user", os.environ.get("SMTP_USER", ""))
        smtp_pass = self.config.get("smtp_pass", os.environ.get("SMTP_PASS", ""))

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["To"] = recipient
            msg["From"] = smtp_user or "approv@localhost"

            if smtp_host != "localhost":
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    if smtp_user:
                        server.login(smtp_user, smtp_pass)
                    server.sendmail(msg["From"], [recipient], msg.as_string())
            else:
                logger.info(f"Email (simulated): to={recipient}, subject={subject}")

            return self.config["outputs"][0], f"Email sent to {recipient}"
        except Exception as e:
            logger.error(f"EmailNotify failed: {e}")
            return self.config["outputs"][0], f"EmailNotify failed (continuing): {e}"


class SMSNotify:
    """Send SMS notification. Config: to_field, message_template. Uses Twilio if configured."""

    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        import os

        to_field = self.config.get("to_field", "phone")
        recipient = form_data.get(to_field, "")
        message = self.config.get("message_template", "Workflow notification")

        try:
            message = message.format(**form_data)
        except KeyError:
            pass

        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_from = os.environ.get("TWILIO_FROM_NUMBER")

        if twilio_sid and twilio_token and twilio_from:
            try:
                from twilio.rest import Client
                client = Client(twilio_sid, twilio_token)
                client.messages.create(body=message, from_=twilio_from, to=recipient)
                return self.config["outputs"][0], f"SMS sent to {recipient}"
            except Exception as e:
                logger.error(f"SMSNotify failed: {e}")
                return self.config["outputs"][0], f"SMSNotify failed (continuing): {e}"
        else:
            logger.info(f"SMS (simulated): to={recipient}, message={message}")
            return self.config["outputs"][0], f"SMS sent to {recipient} (simulated)"


class Cancel:
    """Cancels the workflow."""

    def __init__(self, config: dict):
        self.config = config

    def process(self, form_data: dict) -> tuple[str, str]:
        form_data["_cancelled"] = True
        return "stop", "Workflow cancelled"


# Registry of all step classes by name
STEP_REGISTRY: dict[str, type] = {
    "Start": Start,
    "Stop": Stop,
    "Simple": Simple,
    "ExclusiveChoice": ExclusiveChoice,
    "MultiChoice": MultiChoice,
    "MutexChoice": MutexChoice,
    "RESTCall": RESTCall,
    "EmailNotify": EmailNotify,
    "SMSNotify": SMSNotify,
    "Cancel": Cancel,
}
