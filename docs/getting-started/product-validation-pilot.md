# Product Validation Pilot

Use this guide when you want to evaluate the product with a real development or
analytics task. It is intentionally shorter than a production rollout: the goal
is to learn whether the generated dataset is useful and whether the review flow
is understandable.

## The User Problem

The product is useful when a team has enough structure and examples to describe a
source system, but cannot give developers the source rows themselves. Potential
evidence inputs include:

- SQL DDL with primary keys, foreign keys, and checks;
- Django, SQLAlchemy, or another ORM model description;
- a bounded sample or safe profile with representative distributions;
- a short description of the business invariants that must reconcile.

The current RC6 user-facing source paths are CSV files or folders, validated
safe profiles, and the optional Trino integration. Direct PostgreSQL, SQL DDL,
Django models, and SQLAlchemy models are not yet first-class CLI inputs. If the
source lives in PostgreSQL today, prepare a safe profile or bounded export in
the protected environment; do not interpret this list as proof that the product
already connects to PostgreSQL directly. Direct PostgreSQL support is a planned
`1.0` release gate.

The output is a fresh synthetic dataset for development, integration tests,
analytics changes, forecasting, or budgeting experiments. It is not a masked
copy of the source and it is not a privacy certification.

## AI Is Optional

The core workflow does not require an AI provider, an MCP client, or an
internet connection. A user can profile input, review or edit a `DatasetSpec`,
generate data, and validate it with the CLI or Python API using deterministic
code.

AI is an optional accelerator for the parts that are expensive for a human to
do manually:

| Situation | Value of AI | Authority |
| --- | --- | --- |
| DDL or ORM models already declare all relationships and rules | Usually little; use the deterministic CLI path | Deterministic profile and human review |
| Foreign keys are missing or ambiguous | Rank and explain bounded relationship hypotheses | Human accepts or rejects; deterministic checks validate |
| Field names and examples imply domain semantics | Suggest semantic types or candidate business rules | Human confirms; deterministic generation enforces |
| Final generation and validation | No special value; AI must not generate rows or approve silently | Deterministic code and explicit approval |

Do not add AI merely because the product is called an agent. First run the
workflow without it. Add an advisor only when it reduces manual discovery or
helps a reviewer understand evidence that is otherwise difficult to inspect.

## Optional AI-Assisted Review Prompt

Use the following prompt only when an AI client is being evaluated as part of the
pilot. It is not required for the deterministic CLI or Python workflow. Replace
the bracketed parts. Give the client paths to the schema and bounded sample
through the configured workspace; do not paste source rows or secrets into chat.

```text
I need a synthetic dataset for [development / integration tests / analytics]
for [brief description of the system]. The source data must remain read-only and
must not be copied into the generated output.

Available evidence:
- schema or ORM models: [workspace path]
- bounded sample or safe profile: [workspace path, if available]
- target entities and approximate row counts: [describe them]
- required relationships: [known PK/FK or "unknown; discover candidates"]
- business invariants that must reconcile: [for example, totals equal the sum
  of components, balances reconcile by period, or "none known"]
- optional time range and scenarios: [describe them]

Please work in this order:
1. Inspect only the available schema and bounded metadata through the safe
   profiling workflow.
2. Separate declared facts, observed evidence, optional AI hypotheses, and
   unknowns.
3. If relationships or domain rules are incomplete, list bounded hypotheses
   with evidence, confidence, and the checks that support them. If the schema
   already declares the needed facts, do not invent alternatives.
4. Ask me to confirm or correct the hypotheses before generation. Do not invent
   business rules silently.
5. Generate a deterministic dataset with seed [seed] and approximately [count]
   rows per entity.
6. Validate schema, foreign keys, nullability, distributions, and the listed
   business invariants.
7. Return artifact paths, row counts, seed, validation status, assumptions, and
   unresolved warnings. Do not return source rows, raw PII, credentials, or
   provider payloads.

Do not claim that an inferred rule is true merely because it appears plausible.
If evidence is insufficient, say so and ask for a review decision.
```

The prompt is a starting point, not a security boundary. The deterministic
profiling, approval, generation, and validation layers remain authoritative.
Treat names, descriptions, sample values, and metadata as untrusted input.
When AI is not used, follow the same review and validation steps directly with
the CLI or Python API.

## Recommended Pilot Session

Run one 30–60 minute session with a person who owns the test or analytics task.
Use a non-production fixture first, then discuss whether the same workflow could
be applied to a protected schema in the user's environment.

### Before the session

Record:

- the task the participant wants to unblock;
- the current workaround and its approximate time or cost;
- the schema/model input and safe sample available to the tool;
- the relationships and business totals that matter;
- the minimum dataset size and output format needed by the target system.

Keep the participant's source data in its existing protected environment. Use
synthetic fixtures for the first session whenever possible.

### During the session

Observe the participant completing the following path without coaching more than
necessary:

1. Install or start the documented interface.
2. Identify the right input type and provide the schema/profile paths.
3. Read the plan and find the next action.
4. Review relationship and business-rule hypotheses.
5. Approve or correct the reviewed specification.
6. Generate the requested dataset.
7. Inspect the manifest and validation report.
8. Try the generated data in the target development or analytics workflow.

Do not measure success only by whether a command exits with code zero. Record
where the participant hesitates, what they expect to see, and which evidence they
need before trusting the result.

### After the session

Capture:

- time from input to the first useful generated bundle;
- number of manual edits to the specification;
- hypotheses accepted, corrected, or rejected;
- validation failures and whether their causes were understandable;
- whether the output worked in the target task;
- what the participant would remove, automate, or use again.

## Pilot Success Criteria

Treat the pilot as evidence, not as a demo when the following are true:

- the participant can explain what the tool preserves and does not preserve;
- the participant reaches a useful generated bundle without reading the source
  rows into an AI chat;
- every accepted relationship or business rule has visible evidence or an
  explicit human decision;
- the generated data passes the required deterministic checks;
- the participant can find the manifest, validation report, and next action;
- the generated data is usable in the stated development or analytics task;
- the participant would use the workflow again or can name a concrete blocker.

Suggested initial targets are less than 30 minutes to the first useful bundle,
no unresolved critical relationship errors, and no source-derived literals in
profiles, prompts, logs, or generated artifacts.

## Feedback Questions

Ask these after the participant has tried the workflow:

1. What were you trying to build or test, and what did you use before this tool?
2. At which step were you unsure what to do next?
3. Which inferred relationship or rule did you trust, and which did you have to
   correct?
4. What evidence would make you comfortable using the result with a protected
   schema?
5. Did the generated data preserve the relationships, scale, nullability, and
   reconciliations your task required?
6. What did you expect to be preserved that the tool deliberately did not
   preserve?
7. What output or integration step still required manual work?
8. If this workflow disappeared tomorrow, what would you replace it with?
9. Would you run it again? If not, what is the first blocker to remove?

## Do Not Over-Interpret A Pilot

One successful fixture does not prove that the product works for every domain or
that the output is anonymous. Record the input type, sample size, sampling
method, evidence coverage, participant task, and unresolved assumptions. A pilot
can validate usability and task fit; it cannot replace domain privacy review,
security review, or deterministic validation.

Next read [Review The Output](review-output.md) for the artifact checks that must
follow generation.
