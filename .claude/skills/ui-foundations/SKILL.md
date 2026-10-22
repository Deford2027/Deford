---
name: ui-foundations
description: Design, implement, review, or repair web and app interfaces using rigorous layout, typography, composition, grid, responsive, mobile, accessibility, and visual-QA rules. Use for UI/frontend pages, dashboards, landing pages, design systems, CSS layout, Russian or Cyrillic typography, mobile adaptation, visual hierarchy, responsive behavior, and production-readiness reviews.
---

# UI Foundations

Use this skill as the structural quality floor for interface work. It governs how
content is organized, typeset, adapted, and verified. It does not prescribe a
single visual style, framework, or component library.

## Route the task

Always read the project's existing design system, tokens, components, and
constraints before proposing a new direction. Preserve established decisions
unless the task explicitly calls for a redesign.

Load these references as needed:

- For every design or layout task, read `references/layout.md`,
  `references/composition-grid.md`, and `references/typography.md`.
- For Russian or Cyrillic copy, also read `references/russian-typography.md`.
- For responsive or mobile work, also read `references/responsive-mobile.md`.
- For interactive interfaces, forms, navigation, or audits, also read
  `references/accessibility.md`.
- Before choosing UI or motion dependencies, read `references/libraries.md`.
- Before declaring the work complete, read and execute
  `references/qa-checklist.md`.

## Workflow

1. **Inventory the real content and states.** Identify the primary user goal,
   information priority, required actions, navigation, data density, long-copy
   cases, and loading/empty/error/success states.
2. **Define the hierarchy.** Write down what must be noticed first, second, and
   third. Map each level to position, scale, weight, contrast, grouping, and
   whitespace. Do not use decoration to compensate for unclear hierarchy.
3. **Choose the layout logic.** Establish container behavior, columns, gutters,
   alignment anchors, spacing rhythm, component boundaries, and overflow rules.
   Use normal flow, Grid, and Flexbox before absolute positioning.
4. **Build the type system.** Select fonts with the necessary scripts and real
   weights. Define roles, responsive sizes, line heights, measures, numeric
   treatment, and wrapping behavior.
5. **Design responsive transformations.** Decide what reflows, stacks, wraps,
   condenses, scrolls, becomes a disclosure, or changes navigation pattern.
   Never treat mobile as a uniformly scaled desktop.
6. **Specify interaction and accessibility.** Define semantic controls, focus,
   keyboard behavior, target size, error recovery, motion, reduced-motion
   behavior, and assistive-technology labels.
7. **Implement with the smallest suitable toolset.** Prefer native platform
   capabilities. Add a library only when it solves a concrete behavior,
   accessibility, or maintenance problem.
8. **Verify the rendered result.** Inspect real screenshots at representative
   widths and states. Test zoom, keyboard, long text, reduced motion, and
   overflow. Fix observed defects, not only source-code concerns.

## Non-negotiable quality gates

- Content structure precedes visual styling.
- Every screen has one legible primary hierarchy; repeated cards are not a
  substitute for hierarchy.
- Layout remains usable without horizontal page scrolling at narrow widths,
  except for content that is inherently two-dimensional.
- Breakpoints respond to content failure, not to named device models.
- Text remains readable when zoomed and when user font settings grow.
- Controls remain keyboard-operable, visibly focused, correctly labelled, and
  large enough to target.
- Long localized text, large numbers, missing media, and empty/error states do
  not break the composition.
- Animation communicates state, relationship, or continuity; it is not ambient
  decoration. Reduced-motion preferences are respected.
- The interface uses a coherent spacing and type system instead of isolated
  pixel decisions.
- A task is not complete until the rendered result passes the visual checklist.

## Working with other design skills

- Use `impeccable`, `design-taste-frontend`, or `frontend-design` for art
  direction, distinctiveness, and critique.
- Use `emil-design-eng` for motion and interaction polish.
- Use `adaptive-web-layout` whenever producing or repairing HTML/CSS; follow its
  mobile-first implementation patterns and final layout checklist.
- Use `web-design-guidelines` for a current rule-based final audit.
- Use this skill to enforce the underlying layout, typography, responsive,
  accessibility, and verification baseline across all of them.

When skills disagree, preserve user requirements and project conventions first,
then accessibility and functional clarity, then stylistic preference.
