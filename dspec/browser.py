"""CLI browser — browse specs in the Smalltalk four-pane style."""

from pathlib import Path


def browse_spec(spec: dict):
    """Print a Smalltalk-browser-style view of a spec."""
    obj_name = spec.get("object", "Unknown")
    package = spec.get("package", "(default)")
    purpose = spec.get("purpose", "").strip()

    print(f"\n{'=' * 60}")
    print(f"  {package} >> {obj_name}")
    print(f"{'=' * 60}")
    print(f"  {purpose}")
    print()

    # Data structures (Class pane)
    data = spec.get("data", {})
    print(f"  DATA STRUCTURES ({len(data)})")
    print(f"  {'-' * 40}")
    for name, struct in data.items():
        desc = ""
        if isinstance(struct, dict):
            desc = struct.get("description", "")
            fields = struct.get("fields", {})
            print(f"    {name}  ({len(fields)} fields)  {desc}")
            for fname, ftype in fields.items():
                type_str = ftype if isinstance(ftype, str) else ftype.get("type", "?")
                print(f"      .{fname}: {type_str}")
    print()

    # Protocols (Protocol pane)
    protocols = spec.get("protocols")
    messages = spec.get("messages", {})
    if protocols:
        print(f"  PROTOCOLS")
        print(f"  {'-' * 40}")
        for proto_name, msg_list in protocols.items():
            print(f"    [{proto_name}]")
            for msg_name in msg_list:
                marker = "+" if msg_name in messages else "?"
                print(f"      {marker} {msg_name}")
        print()

    # Messages (Method pane + Code pane)
    print(f"  MESSAGES ({len(messages)})")
    print(f"  {'-' * 40}")
    for msg_name, msg in messages.items():
        desc = msg.get("description", "")
        inp = msg.get("input", {})
        out = msg.get("output", "Void")

        # Signature
        params = ", ".join(f"{k}: {v}" for k, v in inp.items()) if isinstance(inp, dict) else ""
        print(f"    >> {msg_name}({params}) -> {out}")
        if desc:
            print(f"       {desc}")

        # Algorithm
        algo = msg.get("algorithm", [])
        if algo:
            print(f"       algorithm:")
            for i, step in enumerate(algo, 1):
                print(f"         {i}. {step}")

        # Constraints
        constraints = msg.get("constraints", [])
        if constraints:
            print(f"       constraints:")
            for c in constraints:
                print(f"         - {c}")

        # Errors
        errors = msg.get("errors", {})
        if errors:
            print(f"       errors:")
            for err_name, err_desc in errors.items():
                print(f"         ! {err_name}: {err_desc}")
        print()

    # Dependencies
    deps = spec.get("dependencies", {})
    if deps:
        print(f"  DEPENDENCIES ({len(deps)})")
        print(f"  {'-' * 40}")
        for dep_name, dep in deps.items():
            msgs = dep.get("messages", []) if isinstance(dep, dict) else []
            desc = dep.get("description", "") if isinstance(dep, dict) else ""
            print(f"    -> {dep_name}: {', '.join(msgs)}")
            if desc:
                print(f"       {desc}")
        print()

    # Environment
    env = spec.get("environment")
    if env:
        print(f"  ENVIRONMENT")
        print(f"  {'-' * 40}")
        for k, v in env.items():
            if isinstance(v, list):
                print(f"    {k}: {', '.join(v)}")
            else:
                print(f"    {k}: {v}")
        print()

    # Constraints
    constraints = spec.get("constraints", [])
    if constraints:
        print(f"  CONSTRAINTS")
        print(f"  {'-' * 40}")
        for c in constraints:
            print(f"    - {c}")
        print()


def list_specs(directory: str) -> list[Path]:
    """Find all .spec.yml files in a directory tree."""
    root = Path(directory)
    specs = sorted(root.rglob("*.spec.yml"))
    return specs
