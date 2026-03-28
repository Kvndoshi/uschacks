import re

SENSITIVE_ACTIONS = [
    "submit_form", "send_email", "send_message", "make_payment",
    "enter_payment_info", "purchase", "confirm_order", "delete",
    "post_content", "fill_password", "authorize_oauth", "sign_in",
    "create_account", "transfer_funds", "subscribe",
]

SENSITIVE_URL_PATTERNS = [
    r"checkout", r"payment", r"pay\b", r"send\b", r"delete",
    r"confirm", r"submit", r"purchase", r"order", r"subscribe",
    r"login", r"signin", r"auth", r"transfer",
]

SENSITIVE_DOM_KEYWORDS = [
    "password", "credit card", "cvv", "ssn", "social security",
    "billing", "payment method", "confirm purchase",
]


def detect(agent_output: str, url: str = "", dom_context: str = "") -> tuple[bool, str]:
    """Returns (is_sensitive, reason) tuple."""
    output_lower = agent_output.lower()

    for action in SENSITIVE_ACTIONS:
        if action.replace("_", " ") in output_lower or action in output_lower:
            return True, f"Detected sensitive action: {action}"

    for pattern in SENSITIVE_URL_PATTERNS:
        if re.search(pattern, url.lower()):
            return True, f"URL matches sensitive pattern: {pattern}"

    for keyword in SENSITIVE_DOM_KEYWORDS:
        if keyword in dom_context.lower():
            return True, f"DOM contains sensitive content: {keyword}"

    return False, ""
