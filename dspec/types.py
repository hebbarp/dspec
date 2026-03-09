"""Built-in type system for dspec."""

import re

# Primitive types recognized by dspec
PRIMITIVES = {
    "String", "Int", "Integer", "Float", "Double", "Decimal",
    "Boolean", "Bool", "Date", "DateTime", "Time", "Timestamp",
    "UUID", "Void", "Bytes",
}

# Generic wrappers
GENERICS = {"List", "Set", "Map", "Optional"}

# Pattern: PascalCase identifier
PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]+$")

# Pattern: type expression like List<Invoice>, Map<String, Int>, Optional<Session>
TYPE_EXPR = re.compile(
    r"^(List|Set|Optional)<\s*([A-Za-z0-9<>, ]+)\s*>$"
    r"|^Map<\s*([A-Za-z0-9<>, ]+)\s*,\s*([A-Za-z0-9<>, ]+)\s*>$"
    r"|^[A-Z][a-zA-Z0-9]*$"
)


def parse_type(type_str: str) -> tuple[str, list[str]]:
    """Parse a type expression into (base_type, [type_params]).

    Examples:
        'String' -> ('String', [])
        'List<Invoice>' -> ('List', ['Invoice'])
        'Map<String, Int>' -> ('Map', ['String', 'Int'])
        'Optional<Session>' -> ('Optional', ['Session'])
    """
    type_str = type_str.strip()

    # Simple type
    if "<" not in type_str:
        return (type_str, [])

    # Generic type
    base = type_str[:type_str.index("<")]
    inner = type_str[type_str.index("<") + 1 : type_str.rindex(">")].strip()

    if base == "Map":
        # Split on top-level comma only
        depth = 0
        split_at = -1
        for i, ch in enumerate(inner):
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
            elif ch == "," and depth == 0:
                split_at = i
                break
        if split_at == -1:
            return (base, [inner])
        return (base, [inner[:split_at].strip(), inner[split_at + 1:].strip()])

    return (base, [inner])


def extract_referenced_types(type_str: str) -> set[str]:
    """Extract all type names referenced in a type expression.

    Returns only non-primitive, non-generic types (i.e., user-defined data structures).
    """
    base, params = parse_type(type_str)

    refs = set()

    if base not in PRIMITIVES and base not in GENERICS:
        refs.add(base)

    for param in params:
        refs |= extract_referenced_types(param)

    return refs
