import re

# Token type prefix for pandoc divs
PANDOC_DIV = "pandoc_div"

# Regex patterns for attribute parsing
# Matches: {#id .class1 .class2 key="value" key=value}
ATTR_PATTERN = re.compile(
    r"\{\s*"
    r"(?P<attrs>"
    r"(?:"
    r"(?:"
    r"(?:#[\w-]+)|"  # ID: #myid
    r"(?:\.[\w-]+)|"  # Class: .myclass
    r"(?:[\w-]+=(?:\"(?:[^\"\\]|\\.)*\"|'(?:[^\'\\]|\\.)*'|[^\s\"'{}=]+))|"  # Key-value
    r"(?:-)"  # Flag like -
    r")"
    r"[\s]*"
    r")+"
    r")\s*\}"
)

# Simple unbraced class name (e.g., ::: warning)
SIMPLE_CLASS_PATTERN = re.compile(r"^([\w-]+)(?:\s*:*)*$")

_ATTR_TOKEN_RE = re.compile(
    r"(?P<id>#[\w-]+)|"
    r"(?P<class>\.[\w-]+)|"
    r"(?P<key_val>[\w-]+=(?:\"(?:[^\"\\]|\\.)*\"|'(?:[^\'\\]|\\.)*'|[^\s\"'{}=]+))|"
    r"(?P<flag>-)"
)


def _parse_kv(kv_str: str) -> tuple[str, str]:
    key, val = kv_str.split("=", 1)
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].replace('\\"', '"').replace("\\'", "'")
    return key, val


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
    if m := SIMPLE_CLASS_PATTERN.match(attr_string):
        result["classes"] = [m.group(1)]
        return result

    # Handle full brace syntax - strip braces
    if attr_string.startswith("{") and attr_string.endswith("}"):
        attr_string = attr_string[1:-1].strip()

    # Parse individual attributes token-by-token
    classes: list[str] = []
    result["classes"] = classes
    for match in _ATTR_TOKEN_RE.finditer(attr_string):
        if match.group("id"):
            result["id"] = match.group("id")[1:]
        elif match.group("class"):
            classes.append(match.group("class")[1:])
        elif match.group("key_val"):
            key, val = _parse_kv(match.group("key_val"))
            result[key] = val
        elif match.group("flag"):
            classes.append("-")

    return result


def _token_sort_key(tok: str) -> int:
    if tok.startswith("#"):
        return 0
    if tok.startswith("."):
        return 1
    return 2 if tok == "-" else 3


def format_attribute_string(attr_string: str) -> str:
    """Format an attribute string by stripping spaces and single-spacing tokens."""
    attr_string = attr_string.strip()
    if not attr_string:
        return ""

    if m := SIMPLE_CLASS_PATTERN.match(attr_string):
        return f"{{.{m.group(1)}}}"

    if attr_string.startswith("{") and attr_string.endswith("}"):
        attr_string = attr_string[1:-1].strip()

    tokens = [match.group(0) for match in _ATTR_TOKEN_RE.finditer(attr_string)]
    if not tokens:
        return "{}"

    sorted_tokens = sorted(tokens, key=_token_sort_key)
    return "{" + " ".join(sorted_tokens) + "}"


def format_attributes(attrs: str | dict[str, str | list[str]]) -> str:
    """Format attributes back to pandoc syntax.

    Args:
        attrs: An attribute string or a parsed attribute dict.

    Returns:
        Formatted attribute string like {#id .class1 .class2 key="value"}

    """
    if isinstance(attrs, str):
        return format_attribute_string(attrs)

    parts: list[str] = []

    # ID first
    if attrs.get("id"):
        parts.append(f"#{attrs['id']}")

    # Classes
    classes = attrs.get("classes", [])
    if isinstance(classes, list):
        parts.extend(cls if cls == "-" else f".{cls}" for cls in classes)

    # Other key-value attributes
    for key, value in attrs.items():
        if key in ("id", "classes"):
            continue
        if isinstance(value, str):
            if " " in value or '"' in value or "'" in value:
                escaped_value = value.replace('"', '\\"')
                parts.append(f'{key}="{escaped_value}"')
            else:
                parts.append(f"{key}={value}")

    if parts:
        return "{" + " ".join(parts) + "}"
    return ""
