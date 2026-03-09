# dspec — Distributed Object Specification System

Write specs, not code. Think first, implement later.

dspec is a specification discipline tool based on Wirth's principle: **Algorithm + Data Structure = Program**. Developers define objects — their data structures, message protocols, and algorithms — in a structured YAML format. dspec validates completeness and correctness before any implementation begins.

dspec is **not coupled to any LLM or code generator**. It produces structured specs that can be handed to any implementer — human, AI, or toolchain. The implementation is late-bound; the spec is the artifact.

## Inspiration

- **Smalltalk's message passing** — objects respond to messages, organized by protocols
- **Erlang/Elixir distribution** — a mesh of nodes, each hosting objects with specific capabilities
- **DNS hierarchy** — eventually-consistent capability discovery across the network
- **Niklaus Wirth** — programs are algorithms plus data structures, nothing more

## Install

```bash
pip install dspec
```

Or from source:

```bash
git clone https://github.com/hebbarp/dspec.git
cd dspec
pip install -e .
```

## Quick Start

```bash
# Create a new spec
dspec init InvoiceReconciler -p billing

# Edit the spec in your editor...

# Validate it
dspec validate invoice_reconciler.spec.yml

# Browse it (Smalltalk-style four-pane view)
dspec browse invoice_reconciler.spec.yml

# List all specs in a directory
dspec list ./specs

# Export as a structured prompt (for any implementer)
dspec export invoice_reconciler.spec.yml
```

## What a Spec Looks Like

```yaml
object: InvoiceReconciler
package: billing

purpose: >
  Matches bank transactions against outstanding invoices
  using reference codes and fuzzy amount matching.

data:
  Invoice:
    fields:
      id: UUID
      amount: Decimal
      status:
        type: String
        enum: [pending, matched, disputed]

  MatchResult:
    fields:
      invoice: Invoice
      confidence: Float
      match_type:
        type: String
        enum: [exact, fuzzy, partial, none]

protocols:
  queries: [find_unmatched]
  commands: [match, dispute]

messages:
  match:
    input:
      invoices: List<Invoice>
      transactions: List<BankTransaction>
    output: List<MatchResult>
    algorithm:
      - Index transactions by reference prefix into a HashMap
      - For each invoice, look up candidates by prefix
      - Compare amounts within tolerance
      - Sort results by confidence descending
    constraints:
      - O(n log n) time complexity or better
      - Never compare across currencies
```

## The Browser Metaphor

dspec mirrors Smalltalk's four-pane System Browser:

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   Packages   │   Objects    │  Protocols   │   Messages   │
│              │              │              │              │
│ billing    ◄ │ Reconciler ◄ │ commands   ◄ │ match      ◄ │
│ auth         │ LineItem     │ queries      │ dispute      │
│ shipping     │ Payment      │ events       │              │
├──────────────┴──────────────┴──────────────┴──────────────┤
│ Spec Pane                                                 │
│                                                           │
│  >> match(invoices, transactions) -> List<MatchResult>    │
│                                                           │
│  algorithm:                                               │
│    1. Index transactions by reference prefix              │
│    2. For each invoice, look up candidates                │
│    3. Compare amounts within tolerance                    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## What the Validator Checks

- Object names are PascalCase
- Purpose is substantive (≥20 characters)
- Every message has input types, output type, and algorithm steps
- All referenced types exist in the data section
- Protocols reference real messages
- Dependencies declare which messages they send
- Constraints are non-empty

## Philosophy

The spec is the thinking. Implementation is labor. dspec enforces the thinking.

When a developer writes a spec, they must answer:
- What data does this object hold? (data structures)
- What messages does it respond to? (interface)
- How does it respond? (algorithms)
- What must always be true? (constraints)
- What does it depend on? (dependencies)

If you can't answer these, you're not ready to implement — whether by hand or by machine.

## License

MIT
