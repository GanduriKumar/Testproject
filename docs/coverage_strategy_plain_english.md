# Why we have ~606 tests today, and a smarter plan (plain English)

In 60 seconds
- Today: We create ~600 test conversations per business area. That’s thorough but slow and costly.
- Why so many: We try almost every combination of four “dials” (explained below) across six customer behaviors.
- Better plan: Test fewer, smarter examples that still cover the important ground. Keep critical and risky cases.
- Result: 70–85% fewer tests, similar confidence, faster feedback, lower cost.

1) What creates the ~606 tests? The “dials” and behaviors
- The 4 dials (factors):
   - Price sensitivity (low / medium / high)
      - Commerce link: How sensitive the shopper is to price. Affects promotions, discounts, substitutions.
   - Brand bias (none / soft / hard)
      - Commerce link: Preference for a brand. Influences recommendations and acceptable alternatives.
   - Availability (in‑stock / low‑stock / backorder / out‑of‑stock)
      - Commerce link: Whether the item can ship now. Drives delivery promises and substitutions.
   - Policy boundary (within‑policy / near‑limit / out‑of‑policy)
      - Commerce link: Business rules (returns, fraud checks, age limits). Determines what is allowed.

- The 6 behavior types (how customers ask):
   - Happy Path: Straightforward request.
   - Constraint‑heavy: Lots of conditions (price cap, timing, brand).
   - Ambiguous: Vague or unclear ask.
   - Multi‑turn: Needs back‑and‑forth clarification.
   - Corrections: Customer changes their mind.
   - Adversarial/Trap: Tries to break rules or trick the system.

- Why ~606 per domain?
   - Raw combinations per behavior = 3×3×4×3 = 108 (from the 4 dials above).
   - Across 6 behaviors → 6×108 = 648.
   - We remove a few impossible/irrelevant cases (e.g., Happy Path forbids out‑of‑policy), landing around 606 per business area (domain). Some domains may vary a bit.

2) How we optimize (fewer tests) without losing meaningful coverage
- Pairwise coverage (the big win)
   - Idea: Make sure every pair of dials and their values appears at least once somewhere, instead of testing every 4‑way combo.
   - Why this works: Most real problems appear when two things interact (e.g., “out‑of‑stock” AND “near policy limit”). Testing each pair catches the majority of issues with far fewer tests.
   - Simple analogy: Car testing—don’t drive every possible road+weather+tire+fuel combo. Ensure each pair shows up (rain+snow tires, highway+diesel, etc.). You still find key issues.

- Keep the risky stuff heavy
   - We keep more tests where mistakes are costly or likely: policy edges, out‑of‑stock, high price sensitivity.
   - We keep fewer in the “routine” zone (in‑stock and within policy).

- Always‑on anchors (must‑pass set)
   - A small list of non‑negotiable scenarios per domain that we always run. Protects against regressions we already know about.

- Dial‑up where needed
   - For sensitive areas (e.g., safety/fraud), we can use 3‑way coverage on demand while staying lean elsewhere.

- Keep the same guardrails
   - We still block impossible or irrelevant cases. Business rules remain intact.

- Predictable budgets
   - Set simple caps like “≤100 tests per domain” or “≤20 per behavior.” We fit inside these budgets while meeting pairwise coverage and risk priorities.

- Why this doesn’t lose the coverage that matters
   - Guarantees: Every pair of dial values is still tested.
   - Focus: Risky/policy‑sensitive cases stay in.
   - Safety net: Anchors always run; sensitive areas can use 3‑way.
   - Oversight: We monitor results; if we see misses, we dial up locally.

3) What leaders should expect
- Today: ~600 tests/domain → New: ~90–120 tests/domain (pairwise + anchors + risky cases).
- Benefits: 70–85% fewer tests, much faster runs, much lower cost, more frequent testing.
- Confidence: Similar defect‑finding power because we still test all important interactions and keep high‑risk cases.

Clear next steps (simple)
- Pick budgets (e.g., ≤100 per domain) and list 5–10 anchors/domain.
- Mark high‑risk domains/behaviors that get optional 3‑way coverage.
- Pilot on 2–3 domains; compare time/cost and issues found. Roll out if results hold.

Executive talking points
- We’re replacing brute‑force with smart coverage.
- We cover the interactions that actually surface problems.
- Risky and policy‑sensitive cases remain protected.
- We spend less, move faster, and keep the same confidence.
