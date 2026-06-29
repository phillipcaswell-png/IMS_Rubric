---
Document Purpose: Define the active Athena experience design foundation for page identity, hierarchy, and reusable UI language.
Authority: IMS Charter v1.0; ATHENA_ARCHITECTURE.md.
Inputs: ATHENA_ARCHITECTURE.md; ATHENA_DEVELOPMENT_STANDARD.md.
Outputs: Experience implementation guidance for streamlit_app.py and related design-layer standards.
Updated When: Product experience contracts, layout rules, or canonical UI language change.
Does Not Cover: Governance logic, workflow state transitions, service behavior, or database schema.
---

# Athena Design System

## Purpose
Athena should feel like a polished investment intelligence platform: dense enough for analysts, clear enough for fast judgment, and restrained enough to keep governance visible without overwhelming the task.

## Core Principles
- One page, one primary purpose.
- Product identity belongs in the sidebar, not repeated as a large hero in every view.
- The first screen must answer: what needs attention now?
- Tables support tasks; they should not become the whole page.
- Use plain English for analyst actions and state.
- Preserve governed state, but present it with compact hierarchy.

## Page Identity
- Every routed page needs a compact page header.
- Use a title and short subtitle.
- Home is the exception: it can use a dashboard-style greeting and activity-first layout.
- Do not repeat the full Athena brand block inside page bodies.
- Keep route labels stable in the sidebar even when page titles use better analyst language.

## Sidebar Structure
- Sidebar is the permanent brand and navigation anchor.
- Keep brand lockup, route buttons, and one primary action.
- Sidebar should orient the user, not compete with the page body.
- Keep footer text small and informational.

## Dashboard Cards
- Use bordered cards with dark surfaces and restrained padding.
- Each card should show one clear decision state.
- Prefer short labels, strong contrast, and minimal decorative noise.
- Cards should communicate status, next action, and urgency at a glance.

## Status Badges
- Badges must be compact and legible.
- Use color to signal state, not to decorate.
- Reserve gold for primary Athena actions or neutral governance emphasis.
- Prefer concise labels like Strong Candidate, Mixed, Decision Eligible, or Framework Review.

## Action Buttons
- Primary actions should be visually distinct and gold.
- Secondary actions should be quieter and should not compete with the main task.
- A page should expose at most one obvious next step.
- Button labels should describe the analyst action, not the internal system action.

## Right Rail Cards
- Right-rail cards are summary instruments, not secondary pages.
- Use them for portfolio health, lifecycle mix, and recent activity.
- Prefer compact charts, counts, and short legends over long prose.
- Keep the right rail visually balanced and aligned to the main page purpose.

## Typography Hierarchy
- Page titles: large, restrained, and high contrast.
- Subtitles: smaller, quieter, and descriptive.
- Card titles: short and direct.
- Supporting text: muted and concise.
- Use typography to indicate hierarchy before color does.

## Spacing Rules
- Reduce dead vertical space.
- Use compact spacing between the header and first meaningful content.
- Keep cards breathable but not airy.
- Maintain consistent gutters between the main column and the right rail.
- Avoid long blank stretches above tables or forms.

## Progressive Disclosure
- Start with summary and urgency.
- Reveal details only when the analyst asks for them.
- Keep tables available, but do not front-load them when a summary card or queue is more useful.
- Use sections, tabs, and expanders to defer detail until needed.

## Footer
- Use a short governed footer on routed pages.
- Footer copy should reinforce evidence-bounded, reproducible, auditable workflow.
- Keep it small and subtle.

## Implementation Notes
- Centralize repeated UI text and shared visual tokens where it reduces duplication safely.
- Avoid broad refactors that move workflow logic or governance logic.
- Keep UI changes reversible and local to the presentation layer.

## Related Documents

- README.md
- ATHENA_ARCHITECTURE.md
- ATHENA_DEVELOPMENT_STANDARD.md
- design/ATHENA_UX_PRINCIPLES.md
- design/ATHENA_VIEW_MODEL_STANDARD.md
- design/ATHENA_COMPONENT_LIBRARY.md
