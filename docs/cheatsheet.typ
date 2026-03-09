#set page(
  paper: "a4",
  margin: (x: 2cm, y: 1.8cm),
  fill: white,
)

#set text(font: "Segoe UI", size: 10pt, fill: rgb("#333"))
#set par(leading: 0.6em)

#let accent = rgb("#e94560")
#let green = rgb("#2d8a6e")
#let blue = rgb("#2563eb")
#let dimtext = rgb("#888")
#let mono = "Consolas"

#let cmd(body) = {
  box(
    inset: (x: 5pt, y: 3pt),
    fill: rgb("#f5f5f5"),
    radius: 3pt,
    text(font: mono, size: 9pt, fill: rgb("#333"), body)
  )
}

#let step(num, title, body) = {
  grid(
    columns: (28pt, 1fr),
    gutter: 8pt,
    align(center, text(size: 18pt, weight: "bold", fill: accent, str(num))),
    [
      #text(weight: "bold", size: 11pt, title) \
      #text(size: 9.5pt, fill: rgb("#555"), body)
    ]
  )
  v(0.6em)
}

// ── Header ──

#align(center)[
  #text(size: 28pt, weight: "bold", fill: accent)[dspec]
  #v(0.2em)
  #text(size: 12pt, fill: dimtext)[Write the thinking. Let someone else write the code.]
]

#v(1em)
#line(length: 100%, stroke: 0.5pt + rgb("#eee"))
#v(0.8em)

// ── The Idea ──

#text(size: 11pt, fill: rgb("#555"))[
  Before you build anything, describe it. What are the *things* (nouns)?
  What do they *do* (verbs)? What *rules* apply?
  That description is the spec. The spec is dspec.
]

#v(1.2em)

// ── Three Ways to Start ──

#text(size: 14pt, weight: "bold")[How to start]
#v(0.5em)

#step(1, "Tell a story", [
  Just describe what you're building. dspec pulls out the structure. \
  #v(0.3em)
  #cmd[dspec describe] \
  #v(0.2em)
  #text(size: 9pt, fill: dimtext)[
    _"We need to match bank transactions against invoices by reference code.
    If the amount is close enough, mark it matched. Never compare across currencies."_
  ]
  #v(0.2em)
  Nouns become data. Verbs become operations. Rules become constraints.
])

#step(2, "Review and refine", [
  The story generates a scaffold spec with TODOs. Open it, fill in the blanks. \
  #v(0.3em)
  #cmd[dspec validate my_spec.spec.yml] #h(8pt) #text(size: 9pt, fill: green)[checks everything is complete]
])

#step(3, "Hand it off", [
  Export the spec as a prompt for any implementer --- human, AI, or tool. \
  #v(0.3em)
  #cmd[dspec export my_spec.spec.yml] #h(8pt) #text(size: 9pt, fill: green)[ready to implement]
])

#v(0.8em)
#line(length: 100%, stroke: 0.5pt + rgb("#eee"))
#v(0.8em)

// ── What a Spec Looks Like ──

#text(size: 14pt, weight: "bold")[What a spec looks like]
#v(0.5em)

#block(
  width: 100%,
  inset: 14pt,
  fill: rgb("#1a1a2e"),
  radius: 6pt,
  text(font: mono, size: 8.5pt, fill: rgb("#e0e0e0"))[
```
object: InvoiceReconciler          # the thing (noun)
package: billing                    # where it lives

purpose: >                          # what and why
  Matches bank transactions against invoices
  using reference codes and fuzzy amounts.

data:                               # the nouns
  Invoice:
    fields:
      id: UUID
      amount: Decimal
      status: String               # pending | matched | disputed

messages:                           # the verbs
  match:
    input:
      invoices: List<Invoice>
      tolerance: Float
    output: List<MatchResult>
    algorithm:                      # the how
      - Index transactions by reference prefix
      - Compare amounts within tolerance
      - Sort by confidence

constraints:                        # the rules
  - Never compare across currencies
  - Must be idempotent
```
  ]
)

#v(0.8em)
#line(length: 100%, stroke: 0.5pt + rgb("#eee"))
#v(0.8em)

// ── All Commands ──

#text(size: 14pt, weight: "bold")[Commands]
#v(0.5em)

#table(
  columns: (1fr, 1.8fr),
  stroke: none,
  row-gutter: 4pt,
  inset: (x: 0pt, y: 4pt),
  [#cmd[dspec describe]], [Tell your story, get a spec],
  [#cmd[dspec validate file.spec.yml]], [Check the spec is complete],
  [#cmd[dspec browse file.spec.yml]], [Read the spec in a clean view],
  [#cmd[dspec export file.spec.yml]], [Turn spec into an implementation prompt],
  [#cmd[dspec list]], [See all specs in the project],
  [#cmd[dspec crc]], [Open the CRC card board (visual)],
  [#cmd[dspec crc --sync ws:\/\/ip:8090]], [Collaborative board with your team],
  [#cmd[dspec sync]], [Start the collaboration server],
  [#cmd[dspec init Name -p package]], [Blank template (if you prefer structure)],
)

#v(0.8em)
#line(length: 100%, stroke: 0.5pt + rgb("#eee"))
#v(0.8em)

// ── Team Session ──

#text(size: 14pt, weight: "bold")[Team design session]
#v(0.5em)

#text(size: 10pt, fill: rgb("#555"))[
  Open the CRC card board together. Each card is one object in the system.
  Left side: what it does. Right side: who it talks to.
  When you're done discussing, export as specs.
]

#v(0.4em)

#block(
  width: 100%,
  inset: 10pt,
  fill: rgb("#f8f8f8"),
  radius: 6pt,
  stroke: 1pt + rgb("#eee"),
  text(font: mono, size: 8pt)[
```
 ┌──────────────────────────────────────┐
 │  billing   InvoiceReconciler         │
 ├──────────────────────────────────────┤
 │ What it does       │ Who it talks to │
 │  › match()         │  → Notifier     │
 │  › find_unmatched()│  → AuditLog     │
 │  › flag_disputed() │                 │
 ├──────────────────────────────────────┤
 │ Invoice  MatchResult  BankTransaction│
 ├──────────────────────────────────────┤
 │ ! Never compare across currencies    │
 └──────────────────────────────────────┘
```
  ]
)

#v(1.2em)

// ── Footer ──

#align(center)[
  #text(size: 9pt, fill: dimtext)[
    The spec is the thinking. Everything else is labor. \
    #v(0.3em)
    #text(size: 8pt)[github.com/hebbarp/dspec #h(2em) MIT License]
  ]
]
