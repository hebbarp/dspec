"""Story-driven spec generator.

Developer writes a story describing what the system does.
We extract nouns (objects, data) and verbs (messages, operations).

Inspired by Abbott's method (1983) and CRC card discovery:
  - Nouns → Objects and Data Structures
  - Verbs → Messages and Operations
  - Adjectives → Constraints and Attributes

The developer writes naturally. The system finds the spec.
"""

import re
import textwrap


# ── Common words to ignore when extracting nouns/verbs ──

STOP_NOUNS = {
    "i", "we", "it", "they", "he", "she", "you", "one", "ones",
    "thing", "things", "way", "ways", "time", "times", "system",
    "data", "type", "types", "part", "case", "cases", "step",
    "example", "result", "results", "input", "output", "value",
    "values", "error", "errors", "end", "start", "use", "set",
    "need", "lot", "kind", "something", "everything", "nothing",
    "each", "other", "first", "last", "next", "new", "old",
    "same", "different", "many", "few", "all", "some", "any",
    "process", "method", "function", "object", "class", "module",
    "service", "info", "information",
    # Verbs/gerunds that get noun-captured
    "building", "using", "arrives", "looks", "marks", "gets",
    "compares", "sums", "completes", "runs", "makes", "takes",
    "must", "never", "should", "when", "within", "across",
    # Generic words
    "tolerance", "performance", "manual", "review", "batch",
    "multiple", "different", "outstanding", "partial", "team",
}

STOP_VERBS = {
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "having",
    "do", "does", "did", "doing",
    "will", "would", "shall", "should", "may", "might", "can", "could",
    "get", "got", "make", "made", "let", "say", "said",
    "go", "went", "come", "came", "take", "took", "give", "gave",
    "know", "knew", "think", "thought", "see", "saw",
    "want", "need", "use", "used", "try", "tried",
    "keep", "kept", "put", "run", "ran",
}

# Verbs that indicate operations worth capturing
ACTION_VERBS = {
    "match", "find", "search", "lookup", "query", "fetch", "retrieve", "get",
    "create", "build", "generate", "produce", "make", "add", "insert",
    "update", "modify", "change", "edit", "set", "adjust",
    "delete", "remove", "destroy", "cancel", "revoke", "clear",
    "send", "notify", "alert", "email", "publish", "broadcast", "emit",
    "validate", "check", "verify", "confirm", "ensure", "test",
    "calculate", "compute", "sum", "count", "average", "total",
    "import", "export", "load", "save", "store", "persist", "write", "read",
    "sync", "reconcile", "merge", "compare", "diff",
    "transform", "convert", "parse", "format", "serialize", "encode", "decode",
    "filter", "sort", "group", "aggregate", "reduce", "map", "collect",
    "authenticate", "authorize", "login", "logout", "register", "signup",
    "pay", "charge", "refund", "invoice", "bill",
    "ship", "deliver", "track", "dispatch", "route",
    "schedule", "queue", "process", "execute", "handle",
    "lock", "unlock", "block", "unblock", "flag", "mark", "tag", "label",
    "approve", "reject", "review", "assign", "transfer",
    "log", "audit", "record", "monitor", "report",
    "connect", "disconnect", "subscribe", "unsubscribe",
    "encrypt", "decrypt", "hash", "sign",
    "cache", "invalidate", "expire", "refresh",
    "split", "join", "link", "unlink", "bind",
    "allocate", "reserve", "release",
}


def extract_story(text: str) -> dict:
    """Extract nouns, verbs, constraints, and domain from a story.

    Returns a dict with:
      - nouns: list of (noun, context) — candidate objects/data
      - verbs: list of (verb_phrase, subject, object) — candidate messages
      - constraints: list of strings
      - domain: best guess at package name
      - purpose: cleaned up story text
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        sentences = [text.strip()]

    nouns = []
    verbs = []
    constraints = []
    noun_counts = {}

    for sentence in sentences:
        # ── Extract constraints (sentences with must/never/always/should) ──
        if re.search(r'\b(must|never|always|should not|shall not|at most|at least|cannot|no more than|idempotent|atomic|exactly once)\b', sentence, re.I):
            constraints.append(sentence.rstrip('.').strip())

        # ── Extract nouns ──
        # Pattern: "the/a/an NOUN" or "the/a/an ADJECTIVE NOUN"
        for m in re.finditer(r'\b(?:the|a|an|each|every)\s+([a-z]\w+(?:\s+[a-z]\w+){0,2})', sentence, re.I):
            raw = m.group(1).strip().lower()
            words = raw.split()
            # Strip articles, stop words, verb-like words
            ARTICLES = {"the", "a", "an", "this", "that", "its", "their", "our", "my", "his", "her"}
            words = [w for w in words
                     if w not in STOP_NOUNS
                     and w not in ARTICLES
                     and not re.match(r'\w+(ing|ed|es|tion|ment|ly|ness)$', w)
                     and len(w) > 2]
            if words:
                # Strip any remaining articles/determiners
                while words and words[0] in ("the", "a", "an", "this", "that", "its"):
                    words = words[1:]
                if words:
                    clean = " ".join(words[:2])
                    nouns.append((clean, sentence))
                    noun_counts[clean] = noun_counts.get(clean, 0) + 1

        # Compound domain nouns: "invoice number", "payment status", "bank transaction"
        ARTICLES = {"the", "a", "an", "this", "that", "its", "their", "our", "my", "his", "her"}
        for m in re.finditer(r'\b([a-z]{3,})\s+(id|number|code|status|type|name|date|amount|total|count|rate|address|email|token|key|hash|reference|prefix|transaction|invoice|payment|order|user|account|record|item|entry|request|response|message|event|batch|rule|fee|credit|debit)\b', sentence, re.I):
            word1 = m.group(1).lower()
            word2 = m.group(2).lower()
            if word1 not in STOP_NOUNS and word1 not in ARTICLES:
                compound = f"{word1} {word2}"
                nouns.append((compound, sentence))
                noun_counts[compound] = noun_counts.get(compound, 0) + 1

        # ── Extract verb phrases ──
        # Pattern: SUBJECT verbs OBJECT
        for m in re.finditer(r'\b(\w+)\s+({})\w*\s+(?:the\s+)?(\w+(?:\s+\w+)?)'.format(
            "|".join(ACTION_VERBS)
        ), sentence, re.I):
            subject = m.group(1).lower()
            verb = m.group(2).lower()
            obj = m.group(3).strip().lower()
            verbs.append((verb, subject, obj, sentence))

        # Pattern: verb at start of sentence or after "to"
        for m in re.finditer(r'(?:^|\bto\s+)({})\w*\s+(?:the\s+)?(\w+(?:\s+\w+){{0,2}})'.format(
            "|".join(ACTION_VERBS)
        ), sentence, re.I):
            verb = m.group(1).lower()
            obj = m.group(2).strip().lower()
            verbs.append((verb, "", obj, sentence))

    # ── Extract domain/package ──
    domain = "default"
    domain_patterns = [
        re.compile(r'\bfor\s+(?:the\s+)?(\w+)\s+(?:system|service|module|domain|team|department)', re.I),
        re.compile(r'\b(?:billing|auth|shipping|inventory|payment|notification|reporting|analytics|messaging|scheduling)\b', re.I),
    ]
    for pat in domain_patterns:
        m = pat.search(text)
        if m:
            domain = m.group(1).lower() if pat.groups else m.group(0).lower()
            break

    # ── Extract primary object name ──
    # Look for "building a/an X" pattern first, then most-mentioned noun
    primary_name = "NewObject"
    build_match = re.search(r'\bbuilding\s+(?:a|an)\s+(\w+(?:\s+\w+)?)', text, re.I)
    if build_match:
        primary_name = build_match.group(1).strip()
    elif noun_counts:
        ranked = sorted(noun_counts.items(), key=lambda x: -x[1])
        primary_name = ranked[0][0]

    return {
        "primary_name": primary_name,
        "nouns": nouns,
        "noun_counts": noun_counts,
        "verbs": verbs,
        "constraints": constraints,
        "domain": domain,
        "purpose": " ".join(sentences[:3]),
        "sentences": sentences,
    }


def story_to_spec(text: str) -> str:
    """Convert a story into a dspec YAML spec."""
    story = extract_story(text)

    name = _to_pascal_case(story["primary_name"])
    package = story["domain"]
    purpose = story["purpose"]

    # ── Build data structures from nouns ──
    # Rank nouns by frequency, take top ones as data structures
    ranked_nouns = sorted(story["noun_counts"].items(), key=lambda x: -x[1])
    data_types = []
    seen = set()
    for noun, count in ranked_nouns[:6]:  # max 6 data types
        pascal = _to_pascal_case(noun)
        if pascal not in seen and len(pascal) > 2:
            seen.add(pascal)
            # Collect fields from context — look for "noun's X" or "X of noun"
            fields = _extract_fields_for_noun(noun, story["sentences"])
            data_types.append((pascal, fields))

    if not data_types:
        data_types.append((name + "Data", [("id", "UUID")]))

    # ── Build messages from verbs ──
    messages = []
    seen_verbs = set()
    seen_roots = set()  # track root verbs to avoid "match", "match_bank", "match_invoice" all appearing
    for verb, subject, obj, context in story["verbs"]:
        msg_name = _make_message_name(verb, obj)
        if msg_name in seen_verbs or len(msg_name) < 3:
            continue
        # Skip if root verb already seen with a better (longer) name
        root = verb.lower()
        if root in seen_roots:
            continue
        seen_verbs.add(msg_name)
        seen_roots.add(root)
        messages.append({
            "name": msg_name,
            "context": context,
            "verb": verb,
            "object": obj,
        })

    if not messages:
        messages.append({
            "name": "process",
            "context": purpose,
            "verb": "process",
            "object": "",
        })

    # ── Build YAML ──
    y = []
    y.append(f"object: {name}")
    y.append(f"package: {package}")
    y.append("")
    y.append("purpose: >")
    for line in textwrap.wrap(purpose, width=68):
        y.append(f"  {line}")
    y.append("")

    # Data
    y.append("data:")
    for type_name, fields in data_types:
        y.append(f"  {type_name}:")
        y.append(f"    fields:")
        if fields:
            for fname, ftype in fields:
                y.append(f"      {fname}: {ftype}")
        else:
            y.append(f"      id: UUID")
        y.append(f"      # TODO: review and add fields")
    y.append("")

    # Messages
    y.append("messages:")
    for msg in messages[:8]:
        y.append(f"  {msg['name']}:")
        y.append(f"    # from story: \"{msg['context'][:80]}\"")
        y.append(f"    input:")
        y.append(f"      # TODO: what goes in?")
        y.append(f"    output: # TODO: what comes out?")
        y.append(f"    algorithm:")
        y.append(f"      - # TODO: how does it work?")
    y.append("")

    # Constraints
    if story["constraints"]:
        y.append("constraints:")
        for c in story["constraints"]:
            y.append(f"  - {c}")
        y.append("")

    # Environment
    lang = "python"
    lang_match = re.search(r'\b(python|go|rust|java|typescript|javascript|ruby|elixir|c\+\+|csharp|c#)\b', text, re.I)
    if lang_match:
        lang = lang_match.group(1).lower()

    needs = []
    text_lower = text.lower()
    for tool, canonical in [("postgresql", "postgresql"), ("postgres", "postgresql"), ("mysql", "mysql"), ("redis", "redis"), ("mongodb", "mongodb"), ("kafka", "kafka"), ("rabbitmq", "rabbitmq"), ("elasticsearch", "elasticsearch")]:
        if tool in text_lower and canonical not in needs:
            needs.append(canonical)

    y.append("environment:")
    y.append(f"  language: {lang}")
    if needs:
        y.append(f"  needs: [{', '.join(set(needs))}]")
    y.append("  os: any")

    return "\n".join(y)


def describe_interactive() -> str:
    """Conversational mode — ask the developer to tell the story."""
    print()
    print("  Tell me the story of what you're building.")
    print("  " + "─" * 50)
    print("  Write naturally. Use the nouns and verbs you'd")
    print("  use explaining it to a colleague. I'll extract")
    print("  the objects and operations.")
    print()
    print("  (Type your story. Blank line when done.)")
    print()

    lines = []
    while True:
        line = input("  > ")
        if not line.strip():
            if lines:
                break
            continue
        lines.append(line.strip())

    text = " ".join(lines)
    spec = story_to_spec(text)

    print()
    print("  " + "─" * 50)
    print("  Extracted from your story:")
    print()

    # Show what we found
    story = extract_story(text)
    ranked_nouns = sorted(story["noun_counts"].items(), key=lambda x: -x[1])

    print("  NOUNS (objects/data):")
    for noun, count in ranked_nouns[:8]:
        marker = "*" if count > 1 else " "
        print(f"   {marker} {noun} ({count}x)")

    print()
    print("  VERBS (messages):")
    seen = set()
    for verb, subj, obj, ctx in story["verbs"][:8]:
        msg = _make_message_name(verb, obj)
        if msg not in seen:
            seen.add(msg)
            print(f"    > {msg}")

    if story["constraints"]:
        print()
        print("  CONSTRAINTS:")
        for c in story["constraints"]:
            print(f"    ! {c[:70]}")

    print()
    print("  " + "─" * 50)
    print("  Generated spec:")
    print()
    print(spec)

    return spec


def describe_from_text(text: str) -> str:
    """Generate spec from freeform text (non-interactive)."""
    return story_to_spec(text)


# ── Helpers ──

def _to_pascal_case(text: str) -> str:
    words = re.split(r'[\s_\-/]+', text.strip())
    words = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in words if w]
    if not words:
        return "NewObject"
    result = "".join(w.capitalize() for w in words[:3])  # max 3 words
    return result if len(result) > 2 else "NewObject"


def _make_message_name(verb: str, obj: str) -> str:
    """Create a snake_case message name from verb + object."""
    words = [verb.lower()]
    obj_words = obj.split()[:2]
    obj_words = [w.lower() for w in obj_words
                 if w.lower() not in STOP_NOUNS
                 and w.lower() not in ("the", "a", "an", "this", "that", "its", "their")
                 and len(w) > 2]
    words.extend(obj_words)
    result = "_".join(w for w in words if w)
    # Skip useless or nonsensical messages
    if result in ("build", "sum", "bill", "use", "look", "get", "set", "run", "make", "log", "diff", "invoice", "reconcile"):
        return ""
    # Also skip if the verb object is junk
    if any(result.endswith(f"_{w}") for w in ("as", "to", "up", "in", "on", "by", "for")):
        return ""
    if any(w in result for w in ("_the", "the_", "_its", "_this")):
        return ""
    return result


def _extract_fields_for_noun(noun: str, sentences: list[str]) -> list[tuple[str, str]]:
    """Try to find field-like attributes for a noun from context."""
    fields = [("id", "UUID")]
    noun_lower = noun.lower()

    field_patterns = [
        # "invoice amount", "payment date", "user email"
        re.compile(rf'\b{re.escape(noun_lower)}\s+(id|number|code|status|type|name|date|amount|total|count|rate|address|email|token|reference|prefix)\b', re.I),
        # "amount of the invoice", "status of the payment"
        re.compile(rf'\b(id|number|code|status|type|name|date|amount|total|count|rate|address|email|token|reference|prefix)\s+(?:of\s+)?(?:the\s+)?{re.escape(noun_lower)}\b', re.I),
    ]

    seen = {"id"}
    for sentence in sentences:
        for pat in field_patterns:
            for m in pat.finditer(sentence):
                field = m.group(1).lower()
                if field not in seen:
                    seen.add(field)
                    fields.append((field, _guess_type(field)))

    return fields


def _guess_type(field_name: str) -> str:
    """Guess dspec type from a field name."""
    name = field_name.lower()
    if name in ("id", "uuid"):
        return "UUID"
    if name in ("date", "created_at", "updated_at"):
        return "Date"
    if name in ("amount", "total", "rate", "price", "cost"):
        return "Decimal"
    if name in ("count", "number", "quantity"):
        return "Int"
    if name in ("status", "type", "name", "code", "email", "address", "token", "reference", "prefix"):
        return "String"
    return "String"
