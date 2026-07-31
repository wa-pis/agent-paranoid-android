# Design: agent-review-summary

The persisted plan summary gains additive fields with defaults so older
workspaces remain readable. It contains bounded profile-derived names and
types, explicit sensitive flags, relationship endpoints and confidence, and
review guidance.

CLI rendering shows at most eight fields or sensitive references per line.
Control characters are JSON-escaped and long names are truncated. A permanent
warning tells AI clients and humans that entity and field names are untrusted
metadata rather than instructions.
