Athena Development Standard (v1.3.0)

Purpose:
Define the required development and release discipline for Athena capabilities while preserving constitutional boundaries.

Athena Development Cycle:
1. Define problem
2. Freeze constitutional boundaries
3. Freeze architectural boundaries
4. Define measurable success criteria
5. Implement smallest viable capability
6. Validate regression
7. Use on real work
8. Record operational friction
9. Design next MVP

MVP Definition Standard:
- Every MVP must state one objective in plain language.
- Every MVP must define explicit non-objectives.
- Every MVP must define measurable success criteria before implementation.
- Every MVP must name constitutional boundaries that cannot change.
- Every MVP must name architectural boundaries that cannot change.
- Every MVP must identify owner subsystem(s) for each new output field.
- Every MVP must include a verification procedure before approval.

Regression Policy:
- Validation Case 001 remains mandatory for milestone regression safety.
- Regression checks must verify constitutional gates are unchanged unless explicitly governed.
- Regression output must be recorded in repository documentation.
- If regression fails, release progression is blocked until resolved.

Release Policy:
- Release tags must correspond to validated milestone states.
- Documentation updates required by the milestone must be completed before release tag publication.
- No release may include undocumented constitutional behavior changes.
- Release notes must state objective, non-objectives, and verification outcome.

Review Expectations:
- Reviews prioritize constitutional safety over feature completeness.
- Reviewers must verify no unauthorized authority expansion occurred.
- Reviewers must verify ownership provenance for orchestrated outputs.
- Reviewers must verify no governed writes occur in read-only orchestration features.
- Reviewers must confirm residual risks and deferred intentions are documented.
