# Governance

## Project Model

Agent Paranoid Android currently uses a single-maintainer model. The maintainer
owns repository administration, release signing, PyPI and container
publication, security response, roadmap decisions, and final merge authority.
`CODEOWNERS` makes this review responsibility explicit.

Contributors influence decisions through issues, OpenSpec proposals, pull
requests, tests, and review evidence. Technical decisions favor the documented
safety invariants, stable public contracts, small optional integrations, and
deterministic behavior over feature breadth.

## Decision Process

Routine changes may be accepted through normal pull-request review. Changes to
privacy gates, SQL boundaries, public schemas, release infrastructure,
dependencies, or compatibility policy require explicit maintainer review and
relevant safety or contract tests. Larger behavior changes should begin as an
OpenSpec proposal.

The maintainer records material compatibility and security decisions in the
roadmap, OpenSpec, changelog, or security review. When consensus is unavailable,
the maintainer decides and documents the rationale.

## Roles And Succession

Additional maintainers may be invited after sustained, high-quality
contributions and demonstrated judgment around sensitive-data boundaries.
Access should follow least privilege and be reviewed when responsibilities
change.

If the maintainer can no longer operate the project, stewardship may be
transferred to a trusted contributor with a public announcement and secure
rotation of repository, package-index, container-registry, and signing access.
Until such a transfer is announced, forks are independent and must not imply
official release authority.

## Amendments

Governance changes use a normal pull request and must explain their impact on
ownership, security response, and release authority.
