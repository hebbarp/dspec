"""Spec validator — ensures specs are complete and well-formed before routing."""

from dataclasses import dataclass, field
from .types import PRIMITIVES, GENERICS, PASCAL_CASE, parse_type, extract_referenced_types


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)


def validate(spec: dict) -> ValidationResult:
    """Validate a parsed spec dictionary. Returns ValidationResult."""
    result = ValidationResult()

    _check_required_sections(spec, result)
    if not result.valid:
        return result  # Can't continue without required sections

    _check_object_name(spec, result)
    _check_package(spec, result)
    _check_purpose(spec, result)

    defined_types = _check_data(spec, result)
    _check_protocols(spec, result)
    _check_messages(spec, result, defined_types)
    _check_constraints(spec, result)
    _check_environment(spec, result)
    _check_dependencies(spec, result)

    return result


REQUIRED = ["object", "purpose", "data", "messages"]
OPTIONAL = ["package", "protocols", "constraints", "environment", "dependencies"]
ALL_SECTIONS = set(REQUIRED + OPTIONAL)


def _check_required_sections(spec: dict, result: ValidationResult):
    for section in REQUIRED:
        if section not in spec:
            result.error(f"Missing required section: '{section}'")

    for key in spec:
        if key not in ALL_SECTIONS:
            result.warn(f"Unknown section: '{key}' — will be ignored")


def _check_object_name(spec: dict, result: ValidationResult):
    name = spec.get("object", "")
    if not isinstance(name, str):
        result.error("'object' must be a string")
        return
    if not PASCAL_CASE.match(name):
        result.error(f"Object name '{name}' must be PascalCase (e.g., InvoiceReconciler)")


def _check_package(spec: dict, result: ValidationResult):
    pkg = spec.get("package")
    if pkg is None:
        result.warn("No 'package' specified — object will be in the default package")
        return
    if not isinstance(pkg, str):
        result.error("'package' must be a string")
        return
    if not pkg.replace("-", "").replace("_", "").isalpha() or not pkg[0].islower():
        result.error(f"Package name '{pkg}' must be lowercase with hyphens/underscores")


def _check_purpose(spec: dict, result: ValidationResult):
    purpose = spec.get("purpose", "")
    if not isinstance(purpose, str):
        result.error("'purpose' must be a string")
        return
    if len(purpose.strip()) < 20:
        result.error(
            f"Purpose is too short ({len(purpose.strip())} chars). "
            "Write at least 20 characters explaining what this object does and why."
        )


def _check_data(spec: dict, result: ValidationResult) -> set[str]:
    """Validate data structures. Returns set of defined type names."""
    data = spec.get("data", {})
    if not isinstance(data, dict):
        result.error("'data' must be a mapping of structure names to definitions")
        return set()

    defined = set()

    for name, struct in data.items():
        if not PASCAL_CASE.match(name):
            result.error(f"Data structure '{name}' must be PascalCase")
            continue

        defined.add(name)

        if isinstance(struct, dict):
            if "fields" not in struct:
                result.error(f"Data structure '{name}' must have 'fields'")
                continue

            fields = struct["fields"]
            if not isinstance(fields, dict) or len(fields) == 0:
                result.error(f"Data structure '{name}' must have at least one field")
                continue

            for fname, ftype in fields.items():
                if isinstance(ftype, str):
                    _validate_type_expr(ftype, f"{name}.{fname}", result)
                elif isinstance(ftype, dict):
                    if "type" not in ftype:
                        result.error(f"Field '{name}.{fname}' object form must have 'type'")
                    else:
                        _validate_type_expr(ftype["type"], f"{name}.{fname}", result)
                else:
                    result.error(f"Field '{name}.{fname}' must be a type string or object")
        else:
            result.error(f"Data structure '{name}' must be a mapping with 'fields'")

    # Second pass: check that all referenced types are defined or primitive
    all_known = defined | PRIMITIVES | GENERICS
    for name, struct in data.items():
        if not isinstance(struct, dict) or "fields" not in struct:
            continue
        for fname, ftype in struct["fields"].items():
            type_str = ftype if isinstance(ftype, str) else ftype.get("type", "")
            refs = extract_referenced_types(type_str)
            for ref in refs:
                if ref not in all_known:
                    result.warn(
                        f"Type '{ref}' referenced in '{name}.{fname}' "
                        "is not defined in data — may be defined in another object"
                    )

    return defined


def _validate_type_expr(type_str: str, context: str, result: ValidationResult):
    """Check that a type expression is syntactically valid."""
    try:
        base, params = parse_type(type_str)
        if base in GENERICS and len(params) == 0:
            result.error(f"Generic type '{base}' in '{context}' requires type parameters")
        if base == "Map" and len(params) != 2:
            result.error(f"Map in '{context}' requires exactly 2 type parameters: Map<K, V>")
    except (ValueError, IndexError):
        result.error(f"Invalid type expression '{type_str}' in '{context}'")


def _check_protocols(spec: dict, result: ValidationResult):
    protocols = spec.get("protocols")
    if protocols is None:
        result.warn("No 'protocols' defined — consider grouping messages into protocols (queries, commands, events)")
        return

    if not isinstance(protocols, dict):
        result.error("'protocols' must be a mapping of protocol names to message lists")
        return

    messages = set(spec.get("messages", {}).keys())
    all_protocol_messages = set()

    for proto_name, msg_list in protocols.items():
        if not isinstance(msg_list, list):
            result.error(f"Protocol '{proto_name}' must be a list of message names")
            continue
        for msg_name in msg_list:
            if msg_name not in messages:
                result.error(f"Protocol '{proto_name}' references unknown message '{msg_name}'")
            if msg_name in all_protocol_messages:
                result.warn(f"Message '{msg_name}' appears in multiple protocols")
            all_protocol_messages.add(msg_name)

    # Check for messages not in any protocol
    orphans = messages - all_protocol_messages
    for orphan in orphans:
        result.warn(f"Message '{orphan}' is not assigned to any protocol")


def _check_messages(spec: dict, result: ValidationResult, defined_types: set[str]):
    messages = spec.get("messages", {})
    if not isinstance(messages, dict):
        result.error("'messages' must be a mapping of message names to definitions")
        return

    all_known_types = defined_types | PRIMITIVES | GENERICS

    for msg_name, msg in messages.items():
        prefix = f"Message '{msg_name}'"

        if not isinstance(msg, dict):
            result.error(f"{prefix} must be a mapping")
            continue

        # Check required fields
        for req in ["input", "output", "algorithm"]:
            if req not in msg:
                result.error(f"{prefix} missing required field '{req}'")

        # Validate input types
        inp = msg.get("input", {})
        if isinstance(inp, dict):
            for param_name, param_type in inp.items():
                if isinstance(param_type, str):
                    _validate_type_expr(param_type, f"{msg_name}.input.{param_name}", result)
                    refs = extract_referenced_types(param_type)
                    for ref in refs:
                        if ref not in all_known_types:
                            result.warn(
                                f"Type '{ref}' in '{msg_name}.input.{param_name}' "
                                "is not defined in data"
                            )

        # Validate output type
        output = msg.get("output")
        if isinstance(output, str):
            _validate_type_expr(output, f"{msg_name}.output", result)
            refs = extract_referenced_types(output)
            for ref in refs:
                if ref not in all_known_types:
                    result.warn(f"Type '{ref}' in '{msg_name}.output' is not defined in data")

        # Validate algorithm
        algo = msg.get("algorithm")
        if isinstance(algo, list):
            if len(algo) == 0:
                result.error(f"{prefix} algorithm must have at least one step")
            for i, step in enumerate(algo):
                if not isinstance(step, str) or len(step.strip()) == 0:
                    result.error(f"{prefix} algorithm step {i + 1} must be a non-empty string")
        elif algo is not None:
            result.error(f"{prefix} algorithm must be a list of steps")


def _check_constraints(spec: dict, result: ValidationResult):
    constraints = spec.get("constraints")
    if constraints is None:
        result.warn("No 'constraints' defined — consider adding non-functional requirements")
        return
    if not isinstance(constraints, list):
        result.error("'constraints' must be a list of strings")
        return
    for i, c in enumerate(constraints):
        if not isinstance(c, str) or len(c.strip()) == 0:
            result.error(f"Constraint {i + 1} must be a non-empty string")


def _check_environment(spec: dict, result: ValidationResult):
    env = spec.get("environment")
    if env is None:
        result.warn("No 'environment' specified — object can run anywhere")
        return
    if not isinstance(env, dict):
        result.error("'environment' must be a mapping")
        return
    if "language" not in env:
        result.warn("No 'language' in environment — Claude will choose one")


def _check_dependencies(spec: dict, result: ValidationResult):
    deps = spec.get("dependencies")
    if deps is None:
        return
    if not isinstance(deps, dict):
        result.error("'dependencies' must be a mapping of object names to dependency definitions")
        return
    for dep_name, dep in deps.items():
        if not PASCAL_CASE.match(dep_name):
            result.error(f"Dependency '{dep_name}' must be PascalCase")
        if isinstance(dep, dict):
            if "messages" not in dep:
                result.error(f"Dependency '{dep_name}' must list the messages it sends")
            elif not isinstance(dep["messages"], list) or len(dep["messages"]) == 0:
                result.error(f"Dependency '{dep_name}' messages must be a non-empty list")
        else:
            result.error(f"Dependency '{dep_name}' must be a mapping with 'messages'")
