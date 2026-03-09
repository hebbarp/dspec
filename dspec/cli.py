"""dspec CLI — validate, browse, and manage object specs."""

import argparse
import sys
from pathlib import Path

import yaml

from .validator import validate
from .browser import browse_spec, list_specs


def load_spec(path: str) -> dict:
    """Load and parse a YAML spec file."""
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    if not p.suffix in (".yml", ".yaml"):
        print(f"Error: Expected .yml or .yaml file: {path}", file=sys.stderr)
        sys.exit(1)
    with open(p) as f:
        return yaml.safe_load(f)


def cmd_validate(args):
    """Validate one or more spec files."""
    paths = args.files
    all_valid = True

    for path in paths:
        spec = load_spec(path)
        result = validate(spec)

        name = spec.get("object", Path(path).stem)
        if result.valid:
            print(f"  OK  {name} ({path})")
        else:
            print(f"  FAIL  {name} ({path})")
            all_valid = False

        for err in result.errors:
            print(f"    ERROR: {err}")
        if args.warnings:
            for warn in result.warnings:
                print(f"    WARN:  {warn}")

    if not all_valid:
        sys.exit(1)


def cmd_browse(args):
    """Browse a spec in the four-pane view."""
    spec = load_spec(args.file)
    result = validate(spec)

    if not result.valid:
        print("Spec has validation errors — showing anyway.\n")
        for err in result.errors:
            print(f"  ERROR: {err}")
        print()

    browse_spec(spec)


def cmd_list(args):
    """List all specs in a directory."""
    directory = args.directory or "."
    specs = list_specs(directory)

    if not specs:
        print(f"No .spec.yml files found in {directory}")
        return

    print(f"\nSpecs in {directory}:")
    print(f"{'-' * 50}")

    for spec_path in specs:
        try:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)
            name = spec.get("object", "?")
            pkg = spec.get("package", "(default)")
            msgs = len(spec.get("messages", {}))
            result = validate(spec)
            status = "OK" if result.valid else "INVALID"
            print(f"  [{status:>7}]  {pkg}.{name}  ({msgs} messages)  {spec_path}")
        except Exception as e:
            print(f"  [  ERROR]  {spec_path}: {e}")

    print()


def cmd_init(args):
    """Create a new spec file from a template."""
    name = args.name
    package = args.package or "default"
    filename = args.output or f"{name.lower()}.spec.yml"

    if Path(filename).exists():
        print(f"Error: {filename} already exists", file=sys.stderr)
        sys.exit(1)

    template = f"""object: {name}
package: {package}

purpose: >
  TODO: Describe what this object does and why it exists.
  Be specific — at least 20 characters.

data:
  # Define your data structures here
  # Example:
  #   Invoice:
  #     description: An outstanding invoice
  #     fields:
  #       id: UUID
  #       amount: Decimal
  #       status:
  #         type: String
  #         enum: [pending, paid, overdue]
  Item:
    fields:
      id: UUID

protocols:
  queries: []
  commands: []

messages:
  # Define what messages this object responds to
  # Example:
  #   find_by_id:
  #     input:
  #       id: UUID
  #     output: Optional<Item>
  #     algorithm:
  #       - Look up item by ID in the store
  #       - Return None if not found
  example_message:
    input:
      id: UUID
    output: Item
    algorithm:
      - TODO describe your algorithm step by step

constraints:
  - TODO add non-functional requirements

environment:
  language: python
  os: any
"""

    with open(filename, "w") as f:
        f.write(template)

    print(f"Created {filename}")
    print(f"Edit the file, then run: dspec validate {filename}")


def cmd_export(args):
    """Export a spec as a Claude Code prompt."""
    spec = load_spec(args.file)
    result = validate(spec)

    if not result.valid:
        print("ERROR: Spec is invalid. Fix errors before exporting.", file=sys.stderr)
        for err in result.errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    prompt = _spec_to_prompt(spec)
    if args.output:
        with open(args.output, "w") as f:
            f.write(prompt)
        print(f"Exported prompt to {args.output}")
    else:
        print(prompt)


def _spec_to_prompt(spec: dict) -> str:
    """Convert a validated spec into a Claude Code prompt."""
    obj_name = spec["object"]
    package = spec.get("package", "default")
    purpose = spec["purpose"].strip()
    env = spec.get("environment", {})
    language = env.get("language", "the most appropriate language")

    lines = []
    lines.append(f"# Implement: {obj_name}")
    lines.append(f"Package: {package}")
    lines.append(f"Language: {language}")
    lines.append("")
    lines.append(f"## Purpose")
    lines.append(purpose)
    lines.append("")

    # Data structures
    lines.append("## Data Structures")
    lines.append("")
    for name, struct in spec["data"].items():
        desc = struct.get("description", "") if isinstance(struct, dict) else ""
        lines.append(f"### {name}")
        if desc:
            lines.append(desc)
        fields = struct.get("fields", {}) if isinstance(struct, dict) else {}
        for fname, ftype in fields.items():
            if isinstance(ftype, str):
                lines.append(f"- `{fname}`: {ftype}")
            elif isinstance(ftype, dict):
                type_str = ftype.get("type", "?")
                enum_vals = ftype.get("enum")
                default = ftype.get("default")
                desc_str = ftype.get("description", "")
                extra = ""
                if enum_vals:
                    extra += f" (one of: {', '.join(enum_vals)})"
                if default is not None:
                    extra += f" [default: {default}]"
                if desc_str:
                    extra += f" — {desc_str}"
                lines.append(f"- `{fname}`: {type_str}{extra}")
        lines.append("")

    # Messages
    lines.append("## Messages to Implement")
    lines.append("")
    for msg_name, msg in spec["messages"].items():
        desc = msg.get("description", "")
        inp = msg.get("input", {})
        out = msg.get("output", "Void")

        params = ", ".join(f"{k}: {v}" for k, v in inp.items()) if isinstance(inp, dict) else ""
        lines.append(f"### `{msg_name}({params}) -> {out}`")
        if desc:
            lines.append(desc)
        lines.append("")

        algo = msg.get("algorithm", [])
        if algo:
            lines.append("**Algorithm:**")
            for i, step in enumerate(algo, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        constraints = msg.get("constraints", [])
        if constraints:
            lines.append("**Constraints:**")
            for c in constraints:
                lines.append(f"- {c}")
            lines.append("")

        errors = msg.get("errors", {})
        if errors:
            lines.append("**Error conditions:**")
            for err_name, err_desc in errors.items():
                lines.append(f"- `{err_name}`: {err_desc}")
            lines.append("")

    # Global constraints
    constraints = spec.get("constraints", [])
    if constraints:
        lines.append("## Constraints")
        for c in constraints:
            lines.append(f"- {c}")
        lines.append("")

    # Environment
    if env:
        needs = env.get("needs", [])
        if needs:
            lines.append(f"## Required: {', '.join(needs)}")
            lines.append("")

    # Dependencies
    deps = spec.get("dependencies", {})
    if deps:
        lines.append("## External Dependencies (other objects)")
        for dep_name, dep in deps.items():
            msgs = dep.get("messages", []) if isinstance(dep, dict) else []
            desc = dep.get("description", "") if isinstance(dep, dict) else ""
            lines.append(f"- `{dep_name}`: uses messages {', '.join(msgs)}")
            if desc:
                lines.append(f"  {desc}")
        lines.append("")

    lines.append("## Implementation Notes")
    lines.append("- Write clean, idiomatic code with tests")
    lines.append("- Follow the algorithm steps exactly as specified")
    lines.append("- Respect all constraints")
    lines.append("- Handle all listed error conditions")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        prog="dspec",
        description="Distributed Object Specification System — write specs, not code",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # validate
    p_validate = subparsers.add_parser("validate", aliases=["v"], help="Validate spec files")
    p_validate.add_argument("files", nargs="+", help="Spec files to validate")
    p_validate.add_argument("-w", "--warnings", action="store_true", help="Show warnings")
    p_validate.set_defaults(func=cmd_validate)

    # browse
    p_browse = subparsers.add_parser("browse", aliases=["b"], help="Browse a spec")
    p_browse.add_argument("file", help="Spec file to browse")
    p_browse.set_defaults(func=cmd_browse)

    # list
    p_list = subparsers.add_parser("list", aliases=["ls"], help="List specs in a directory")
    p_list.add_argument("directory", nargs="?", help="Directory to search (default: current)")
    p_list.set_defaults(func=cmd_list)

    # init
    p_init = subparsers.add_parser("init", help="Create a new spec from template")
    p_init.add_argument("name", help="Object name (PascalCase)")
    p_init.add_argument("-p", "--package", help="Package name")
    p_init.add_argument("-o", "--output", help="Output filename")
    p_init.set_defaults(func=cmd_init)

    # export
    p_export = subparsers.add_parser("export", aliases=["x"], help="Export spec as Claude prompt")
    p_export.add_argument("file", help="Spec file to export")
    p_export.add_argument("-o", "--output", help="Output file (default: stdout)")
    p_export.set_defaults(func=cmd_export)

    # crc
    p_crc = subparsers.add_parser("crc", help="Open CRC card designer in browser")
    p_crc.add_argument("files", nargs="*", help="Spec files to preload")
    p_crc.add_argument("--port", type=int, default=8089, help="Port (default: 8089)")
    p_crc.add_argument("--sync", help="WebSocket sync URL (e.g., ws://192.168.1.10:8090)")
    p_crc.set_defaults(func=cmd_crc)

    # sync
    p_sync = subparsers.add_parser("sync", help="Start sync server for collaborative editing")
    p_sync.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    p_sync.add_argument("--port", type=int, default=8090, help="Port (default: 8090)")
    p_sync.set_defaults(func=cmd_sync)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


def cmd_crc(args):
    """Launch the CRC card designer in a browser."""
    import http.server
    import webbrowser
    import threading
    import json
    import urllib.parse

    ui_dir = Path(__file__).parent.parent / "ui"
    crc_html = ui_dir / "crc.html"

    if not crc_html.exists():
        print(f"Error: CRC UI not found at {crc_html}", file=sys.stderr)
        sys.exit(1)

    # Preload specs if provided
    preload_cards = []
    for filepath in (args.files or []):
        spec = load_spec(filepath)
        card = spec_to_crc_card(spec)
        preload_cards.append(card)

    class CRCHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ui_dir), **kw)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == '/api/preload':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(preload_cards).encode())
                return
            super().do_GET()

        def log_message(self, format, *a):
            pass  # Suppress request logs

    port = args.port
    server = http.server.HTTPServer(('127.0.0.1', port), CRCHandler)

    sync_url = getattr(args, 'sync', None) or ''
    url = f"http://127.0.0.1:{port}/crc.html"
    if sync_url:
        url += f"?sync={sync_url}"
    print(f"CRC Card Designer running at {url}")
    if preload_cards:
        print(f"Preloaded {len(preload_cards)} specs")
    if sync_url:
        print(f"Syncing with {sync_url}")
    print("Press Ctrl+C to stop\n")

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


def spec_to_crc_card(spec: dict) -> dict:
    """Convert a dspec YAML spec into a CRC card data structure."""
    messages = []
    for msg_name, msg in spec.get("messages", {}).items():
        inp = msg.get("input", {})
        params = ", ".join(f"{k} {v}" for k, v in inp.items()) if isinstance(inp, dict) else ""
        algo_steps = msg.get("algorithm", [])
        messages.append({
            "name": msg_name,
            "params": params,
            "returnType": msg.get("output", "Void"),
            "algorithm": "; ".join(algo_steps) if isinstance(algo_steps, list) else "",
        })

    collaborators = []
    for dep_name, dep in spec.get("dependencies", {}).items():
        msgs = dep.get("messages", []) if isinstance(dep, dict) else []
        collaborators.append({"name": dep_name, "messages": msgs})

    data = []
    for name, struct in spec.get("data", {}).items():
        fields = []
        if isinstance(struct, dict):
            for fname, ftype in struct.get("fields", {}).items():
                type_str = ftype if isinstance(ftype, str) else ftype.get("type", "?")
                fields.append({"name": fname, "type": type_str})
        data.append({"name": name, "fields": fields})

    env = spec.get("environment", {})
    environment = []
    if isinstance(env, dict):
        if env.get("language"):
            environment.append(env["language"])
        environment.extend(env.get("needs", []))

    return {
        "name": spec.get("object", "Unknown"),
        "package": spec.get("package", "default"),
        "purpose": spec.get("purpose", "").strip(),
        "data": data,
        "messages": messages,
        "collaborators": collaborators,
        "constraints": spec.get("constraints", []) or [],
        "environment": environment,
    }


def cmd_sync(args):
    """Start the WebSocket sync server for collaborative editing."""
    import asyncio
    from .sync import run_server
    try:
        asyncio.run(run_server(args.host, args.port))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
