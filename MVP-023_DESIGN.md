# MVP-023 Design Container
Implements: THEIA_SPECIFICATION.md

Constitutional boundaries: See THEIA_SPECIFICATION.md — not restated here.

---

## Purpose
Introduce Theia's first operational Capability by allowing analysts to obtain advisory extraction assistance from promoted evidence without creating or modifying any governed records.

This MVP establishes Extraction and Passage Detection as Theia Capabilities while preserving analyst authorship of all governed observations.

---

## Scope
MVP-023 adds only:

- Extraction Capability
- Passage Detection Capability
- Ephemeral suggestion panel
- Advisory pillar signals
- Advisory confidence level
- Blank Observation Form launch

This MVP does not include:

- Evidence ingestion
- Pipeline orchestration
- Workspace redesign
- Additional evidence sources
- Automatic observation creation

---

## Theia Component
Capability

Capabilities implemented:

- Extraction
- Passage Detection

Current maturity:

Level 0 (Planned)

Target after successful implementation and validation:

Level 1 (Experimental)

---

## Advisory Outputs
The capability may surface:

- Suggested passages
- Advisory pillar signal
- Advisory confidence
- Source location

The capability must never surface:

- Scores
- Recommendations
- Investment conclusions
- Governed observations

---

## Design Constraints
- Ephemeral suggestions only
- Blank observation form
- pillar_id pre-populate permitted
- observation_text never pre-populated
- No suggestion text enters governed fields
- No suggestion output stored
- No suggestion output logged
- Invocation event may be logged

---

## User Experience
1. Analyst selects promoted evidence.
2. Analyst invokes Extraction Capability.
3. Theia displays advisory suggestions.
4. Analyst reviews suggestions.
5. Analyst selects "Open Observation Form."
6. Blank observation form opens.
7. pillar_id may already be selected.
8. Analyst independently authors observation.
9. Existing MVP-022 governed observation workflow continues unchanged.

---

## Service Expectations
New advisory service:

- get_extraction_suggestions(...)

Characteristics:

- Read-only
- Non-governed
- Returns ephemeral advisory output
- Creates no governed records

No implementation details.

No prompt design.

No algorithms.

---

## UI Expectations
Minimal UI additions only:

- Extraction panel
- Advisory suggestion list
- Advisory pillar signal
- Advisory confidence
- Open Observation Form button

No redesign of the Evidence tab.

---

## Non-Goals
- No AI authored observations
- No evidence ingestion
- No pipeline
- No promotion automation
- No scoring
- No recommendations
- No workspace redesign

---

## Verification Requirements
Implementation is complete only when all are true:

- Suggestions generated only from promoted evidence
- Suggestions disappear after session ends
- Observation form opens blank
- observation_text always empty
- pillar_id may be pre-populated
- No governed records written
- No suggestion text stored
- Only invocation events logged
- Existing MVP-022 workflow unchanged
- Validation Case 002 executes successfully using Kodak evidence

---

## MVP-Specific Risks
- Analyst over-reliance on advisory output
- Suggestion quality variance
- UI confusion between advisory and governed information
- Accidental future pressure to pre-populate observation_text

---

## Do-Not-Build Warnings
Do not:

- Pre-populate observation_text
- Store suggestions
- Log suggestion output
- Infer publication dates
- Create observations automatically
- Expand into MVP-024 functionality
- Expand into MVP-025 functionality
- Expand into MVP-026 functionality
