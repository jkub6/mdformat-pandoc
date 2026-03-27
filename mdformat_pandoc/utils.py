import re

# Token type prefix for pandoc divs
PANDOC_DIV = "pandoc_div"

# Regex patterns for attribute parsing
# Matches: {#id .class1 .class2 key="value" key=value}
ATTR_PATTERN = re.compile(
    r"\{\s*"
    r"(?P<attrs>"
    r"(?:"
    r"(?:#[\w-]+)|"  # ID: #myid
    r"(?:\.[\w-]+)|"  # Class: .myclass
    r"(?:[\w-]+=(?:\"[^\"]*\"|'[^']*'|[\w-]+))"  # Key-value: key="val" or key=val
    r"[\s]*"
    r")+"
    r")\s*\}"
)

# Simple unbraced class name (e.g., ::: warning)
SIMPLE_CLASS_PATTERN = re.compile(r"^[\w-]+$")


def parse_attributes(attr_string: str) -> dict[str, str | list[str]]:
    """Parse pandoc attribute string into a structured dict.

    Args:
        attr_string: The attribute string, either:
            - Full syntax: {#id .class1 .class2 key="value"}
            - Simple class: warning

    Returns:
        Dict with 'id', 'classes' (list), and other key-value pairs.
    """
    result: dict[str, str | list[str]] = {"id": "", "classes": []}

    attr_string = attr_string.strip()

    # Handle simple unbraced class name
    if SIMPLE_CLASS_PATTERN.match(attr_string):
        result["classes"] = [attr_string]
        return result

    # Handle full brace syntax - strip braces
    if attr_string.startswith("{") and attr_string.endswith("}"):
        attr_string = attr_string[1:-1].strip()

    # Parse individual attributes
    # ID: #identifier
    for match in re.finditer(r"#([\w-]+)", attr_string):
        result["id"] = match.group(1)

    # Classes: .classname
    classes: list[str] = []
    for match in re.finditer(r"\.([\w-]+)", attr_string):
        classes.append(match.group(1))
    result["classes"] = classes

    # Key-value pairs: key="value" or key='value' or key=value
    for match in re.finditer(
        r"([\w-]+)=(?:\"([^\"]*)\"|'([^']*)'|([\w-]+))", attr_string
    ):
        key = match.group(1)
        # Get whichever group matched
        value = match.group(2) or match.group(3) or match.group(4) or ""
        result[key] = value

    return result


def format_attributes(attrs: dict[str, str | list[str]]) -> str:
    """Format parsed attributes back to pandoc syntax.

    Args:
        attrs: Parsed attribute dict from parse_attributes.

    Returns:
        Formatted attribute string like {#id .class1 .class2 key="value"}
    """
    parts: list[str] = []

    # ID first
    if attrs.get("id"):
        parts.append(f"#{attrs['id']}")

    # Classes
    classes = attrs.get("classes", [])
    if isinstance(classes, list):
        for cls in classes:
            parts.append(f".{cls}")

    # Other key-value attributes
    for key, value in attrs.items():
        if key in ("id", "classes"):
            continue
        if isinstance(value, str):
            escaped_value = value.replace('"', '\\"')
            parts.append(f'{key}="{escaped_value}"')

    if parts:
        return "{" + " ".join(parts) + "}"
    return ""
