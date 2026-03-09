#set page(
  paper: "a4",
  margin: (x: 1.4cm, y: 1.4cm),
  fill: rgb("#fafafa"),
)

#set text(font: "Segoe UI", size: 9pt, fill: rgb("#222"))
#set par(leading: 0.5em)

// ── Styles ──
#let accent = rgb("#e94560")
#let green = rgb("#2d8a6e")
#let blue = rgb("#2563eb")
#let orange = rgb("#c05621")
#let dimtext = rgb("#666")
#let codebg = rgb("#f0f0f0")

#let section-title(body) = {
  v(0.4em)
  block(
    width: 100%,
    inset: (x: 8pt, y: 5pt),
    fill: accent,
    radius: 3pt,
    text(fill: white, weight: "bold", size: 10pt, body)
  )
  v(0.2em)
}

#let subsection(body) = {
  v(0.2em)
  text(fill: accent, weight: "bold", size: 9.5pt, body)
  v(0.1em)
}

#let cmd(body) = {
  box(
    inset: (x: 4pt, y: 2pt),
    fill: codebg,
    radius: 2pt,
    text(font: "Consolas", size: 8pt, fill: rgb("#333"), body)
  )
}

#let codeblock(body) = {
  block(
    width: 100%,
    inset: 8pt,
    fill: rgb("#1a1a2e"),
    radius: 4pt,
    text(font: "Consolas", size: 7.5pt, fill: rgb("#e0e0e0"), body)
  )
}

#let note(body) = {
  block(
    width: 100%,
    inset: (x: 8pt, y: 5pt),
    fill: rgb("#fff8e1"),
    stroke: (left: 3pt + orange),
    radius: (right: 3pt),
    text(size: 8pt, fill: rgb("#5d4037"), body)
  )
}

// ════════════════════════════════════════════════════
// HEADER
// ════════════════════════════════════════════════════

#align(center)[
  #text(size: 22pt, weight: "bold", fill: accent)[dspec] #text(size: 22pt, weight: "light", fill: dimtext)[cheatsheet]
  #v(0.1em)
  #text(size: 9pt, fill: dimtext)[Distributed Object Specification System --- write specs, not code]
  #v(0.1em)
  #text(size: 7.5pt, fill: dimtext)[Wirth's Principle: Algorithm + Data Structure = Program #h(1em) | #h(1em) v0.1.0]
]

#v(0.3em)
#line(length: 100%, stroke: 0.5pt + rgb("#ddd"))
#v(0.2em)

// ════════════════════════════════════════════════════
// TWO COLUMN LAYOUT
// ════════════════════════════════════════════════════

#columns(2, gutter: 14pt)[

// ── CLI COMMANDS ──
#section-title[CLI Commands]

#table(
  columns: (auto, 1fr),
  stroke: none,
  row-gutter: 2pt,
  inset: (x: 4pt, y: 3pt),
  [#cmd[dspec init Name -p pkg]], [Create spec from template],
  [#cmd[dspec validate file.spec.yml]], [Validate a spec],
  [#cmd[dspec validate \*.spec.yml -w]], [Validate with warnings],
  [#cmd[dspec browse file.spec.yml]], [Four-pane Smalltalk view],
  [#cmd[dspec list ./specs]], [List all specs in directory],
  [#cmd[dspec export file.spec.yml]], [Export as structured prompt],
  [#cmd[dspec export file.spec.yml -o f.md]], [Export to file],
  [#cmd[dspec crc]], [Open CRC card designer],
  [#cmd[dspec crc specs/\*.yml]], [CRC with preloaded specs],
  [#cmd[dspec crc --sync ws:\/\/ip:8090]], [CRC with live collaboration],
  [#cmd[dspec sync --port 8090]], [Start sync server on network],
)

// ── SPEC FORMAT ──
#section-title[Spec Format (.spec.yml)]

#codeblock[
```
object: InvoiceReconciler     # PascalCase
package: billing               # lowercase

purpose: >
  What it does and why. Min 20 chars.
  Forces you to think before building.

data:
  Invoice:                     # PascalCase
    description: Optional text
    fields:
      id: UUID                 # simple type
      amount: Decimal
      items: List<LineItem>    # generic
      status:                  # rich type
        type: String
        enum: [pending, matched]
        default: pending

protocols:
  queries: [find_unmatched]
  commands: [match, dispute]
  events: [on_complete]

messages:
  match:
    input:
      invoices: List<Invoice>
      tolerance: Float
    output: List<MatchResult>
    algorithm:
      - Index transactions by prefix
      - Compare amounts within tolerance
      - Sort by confidence descending
    constraints:
      - O(n log n) or better
    errors:
      currency_mismatch: Never compare
        across currencies

constraints:                   # global
  - All operations idempotent
  - Currency mismatches must fail

environment:
  language: python
  runtime: python-3.12
  needs: [postgresql, redis]
  os: any                      # linux|macos|windows|any

dependencies:
  Notifier:
    description: Sends alerts
    messages: [send_alert, send_summary]
```
]

// ── BUILT-IN TYPES ──
#section-title[Type System]

#subsection[Primitives]
#cmd[String] #cmd[Int] #cmd[Float] #cmd[Decimal] #cmd[Boolean] #cmd[Date] #cmd[DateTime] #cmd[Time] #cmd[UUID] #cmd[Void] #cmd[Bytes]

#v(0.3em)
#subsection[Generics]
#table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 4pt, y: 2pt),
  [#cmd[List\<T\>]], [Ordered collection],
  [#cmd[Set\<T\>]], [Unique collection],
  [#cmd[Map\<K, V\>]], [Key-value mapping],
  [#cmd[Optional\<T\>]], [Nullable value],
)

#v(0.3em)
#subsection[User-defined]
Any PascalCase name defined in #cmd[data:] becomes a type.
Reference across objects --- validator warns but allows it.

// ── VALIDATOR RULES ──
#section-title[What the Validator Checks]

#table(
  columns: (auto, 1fr),
  stroke: none,
  row-gutter: 1pt,
  inset: (x: 4pt, y: 3pt),
  text(fill: accent, weight: "bold")[ERROR], [Blocks the spec],
  text(fill: orange, weight: "bold")[WARN], [Allowed but flagged],
)

#v(0.2em)
*Errors (must fix):*
- Object name not PascalCase
- Purpose shorter than 20 characters
- Missing required sections: #cmd[object] #cmd[purpose] #cmd[data] #cmd[messages]
- Data structure without #cmd[fields]
- Message missing #cmd[input], #cmd[output], or #cmd[algorithm]
- Empty algorithm (zero steps)
- #cmd[Map] without exactly 2 type params
- Generic type without type params
- Protocol referencing unknown message
- Dependency without #cmd[messages] list

*Warnings (should review):*
- No #cmd[package] defined
- No #cmd[protocols] defined
- No #cmd[constraints] defined
- No #cmd[environment] defined
- Type referenced but not in #cmd[data]
- Message not in any protocol
- Unknown top-level section

// ── CRC CARD DESIGNER ──
#section-title[CRC Card Designer]

#subsection[Card Layout (Kent Beck / Ward Cunningham)]
#block(
  width: 100%,
  inset: 6pt,
  fill: codebg,
  radius: 4pt,
  text(font: "Consolas", size: 7pt)[
```
 ┌──────────────────────────────────────┐
 │ PACKAGE        ObjectName            │
 ├──────────────────────────────────────┤
 │ Purpose (italic, why it exists)      │
 ├──────────────────┬───────────────────┤
 │ Responsibilities │ Collaborators     │
 │  › match()→Res   │  → Notifier      │
 │  › find()→List   │    send_alert    │
 │  › dispute()     │  → AuditLog      │
 ├──────────────────┴───────────────────┤
 │ [Invoice] [MatchResult] [Payment]    │
 ├──────────────────────────────────────┤
 │ ! Constraint 1                       │
 │ ! Constraint 2                       │
 ├──────────────────────────────────────┤
 │ python  postgresql  redis            │
 └──────────────────────────────────────┘
```
  ]
)

#subsection[Edit Mode Input Formats]

*Data Structures* (one per line):
#codeblock[Invoice: id UUID, amount Decimal, status String]

*Messages* (one per line):
#codeblock[match(invoices List\<Invoice\>) -> List\<Result\> | Index by prefix; Compare amounts; Sort]

*Collaborators* (one per line):
#codeblock[Notifier: send_alert, send_summary]

#subsection[Keyboard Shortcuts]
#table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 4pt, y: 2pt),
  [#cmd[Ctrl+Enter]], [Save card],
  [#cmd[Escape]], [Cancel edit / close modal],
  [Click collaborator], [Jump to that card],
  [Show Links], [Draw dependency arrows],
)

// ── COLLABORATION ──
#section-title[Network Collaboration]

#subsection[Setup (any machine on the network)]
#codeblock[
\# Machine A: start sync server
dspec sync --port 8090

\# Machine A: open board
dspec crc --sync ws:\/\/192.168.1.10:8090

\# Machine B (any OS): join
dspec crc --sync ws:\/\/192.168.1.10:8090

\# Machine C: also joins
dspec crc --sync ws:\/\/192.168.1.10:8090
]

#note[Install #cmd[pip install websockets] on the sync server machine. CRC clients need no extra dependencies --- sync runs over the browser's built-in WebSocket.]

// ── WORKFLOW ──
#section-title[Daily Workflow]

#block(inset: (x: 4pt))[
  #set text(size: 8.5pt)
  #text(fill: green, weight: "bold")[1.] #text(weight: "bold")[Think] --- create spec with #cmd[dspec init] or CRC board \
  #text(fill: green, weight: "bold")[2.] #text(weight: "bold")[Discuss] --- team reviews CRC cards together \
  #text(fill: green, weight: "bold")[3.] #text(weight: "bold")[Validate] --- run #cmd[dspec validate -w] \
  #text(fill: green, weight: "bold")[4.] #text(weight: "bold")[Export] --- #cmd[dspec export] produces implementation prompt \
  #text(fill: green, weight: "bold")[5.] #text(weight: "bold")[Implement] --- hand to any implementer (human, LLM, tool) \
  #text(fill: green, weight: "bold")[6.] #text(weight: "bold")[Verify] --- check implementation against spec constraints
]

#v(0.4em)
#note[dspec is *not* coupled to any LLM. The spec is the artifact. Implementation is late-bound --- like dynamic dispatch in Smalltalk.]

// ── SMALLTALK BROWSER MAPPING ──
#section-title[Smalltalk Browser Mapping]

#table(
  columns: (1fr, 1fr),
  stroke: 0.5pt + rgb("#ddd"),
  inset: (x: 6pt, y: 4pt),
  fill: (x, y) => if y == 0 { rgb("#f0f0f0") } else { none },
  [*Squeak Pane*], [*dspec Equivalent*],
  [Package], [#cmd[package:] domain],
  [Class], [#cmd[object:] spec],
  [Protocol], [#cmd[protocols:] grouping],
  [Method], [#cmd[messages:] handler],
  [Code pane], [algorithm + constraints],
)

#v(0.5em)
#align(center)[
  #text(size: 7pt, fill: dimtext)[
    dspec v0.1.0 #h(1em) | #h(1em) github.com/hebbarp/dspec #h(1em) | #h(1em) MIT License
  ]
]

]
