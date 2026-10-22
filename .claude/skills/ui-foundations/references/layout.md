# Layout

## Select the right layout mechanism

- Start with semantic document order and normal flow. The visual order should
  not contradict keyboard or reading order.
- Use Flexbox for one-dimensional distribution and alignment.
- Use Grid when rows and columns must coordinate.
- Use multicolumn layout only for flowing editorial copy, not application UI.
- Reserve absolute or fixed positioning for overlays, badges, anchored
  decoration, and intentionally detached controls. Do not build the primary
  page structure with coordinates.

## Size intrinsically

- Prefer `min()`, `max()`, `clamp()`, `minmax()`, `fit-content`, `auto-fit`,
  `auto-fill`, and content-aware sizing over long breakpoint ladders.
- Let content determine minimum viable sizes. In grid and flex children, check
  `min-width: 0` and wrapping before hiding overflow.
- Give text containers a readable `max-inline-size`; do not let prose span an
  unlimited widescreen viewport.
- Use `aspect-ratio` for media whose geometry is known, and reserve space to
  prevent layout shift.
- Use logical properties when the product may support multiple writing
  directions.

## Containers, rhythm, and spacing

- Define a page container with fluid side padding and a deliberate maximum
  width. Full-bleed regions may escape it, but their inner content should return
  to an alignment anchor.
- Choose a compact spacing scale, commonly based on 4 px with important
  intervals on an 8 px rhythm. Treat it as a vocabulary, not a law.
- Space according to relationship: related items closer, groups farther apart.
  Section spacing should exceed component-internal spacing.
- Use `gap` for repeated sibling relationships. Avoid stacking arbitrary
  margins that create accidental collapse or inconsistent rhythm.
- Prefer container queries for reusable components whose behavior depends on
  their allocated space, not the global viewport.

## Overflow

- Decide overflow per axis and per content type. Text should wrap; identifiers
  may break safely; tables and code may use a clearly signalled internal
  scroller.
- Do not use `overflow: hidden` to conceal a layout defect.
- Sticky and fixed regions must not cover focused content, headings reached by
  anchors, alerts, or the on-screen keyboard.

## Sources

- [MDN: CSS layout](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout)
- [Every Layout](https://every-layout.dev/)
- [GOV.UK Design System: Layout](https://design-system.service.gov.uk/styles/layout/)
- [GOV.UK Design System: Spacing](https://design-system.service.gov.uk/styles/spacing/)
- [Utopia fluid scales](https://utopia.fyi/)
