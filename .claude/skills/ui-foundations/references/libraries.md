# UI and motion library decisions

Select a dependency only after identifying the concrete problem it solves. A
library does not replace visual hierarchy, content design, CSS competence, or
rendered QA.

## Default decision order

1. Use semantic HTML and modern CSS for layout and ordinary controls.
2. Reuse the project's existing tokens and component system.
3. Add an unstyled or lightly styled accessible primitive when the behavior is
   complex: dialog, combobox, menu, tooltip, tabs, or focus management.
4. Add a visual component kit only when its conventions match the product and
   the team can maintain the customization.
5. Add a motion library only for choreography that CSS or the platform cannot
   express cleanly.

## Suitable tools

- **CSS Grid, Flexbox, container queries:** primary layout tools.
- **Radix Primitives, React Aria, Base UI:** accessible behavioral foundations
  for React interfaces; evaluate framework fit and bundle cost.
- **shadcn/ui:** editable component source and useful starting patterns. Apply
  the product's tokens and art direction; do not ship the default look
  unexamined.
- **Material, Carbon, GOV.UK Design System:** strong choices when the product,
  organization, or regulatory context fits the system.
- **Motion:** state transitions and component-level React animation with
  reduced-motion support.
- **GSAP:** complex marketing sequences and timeline choreography where its
  weight and imperative model are justified.
- **Utopia:** a method and calculator for fluid type and spacing, not a runtime
  requirement.

## Avoid

- Mixing multiple component systems on one surface.
- Adding a dependency for a single simple transition or layout.
- Replacing native links and buttons with generic clickable containers.
- Copying a library demo without adapting semantics, states, copy, density,
  tokens, and responsive behavior.
- Using animation to conceal latency or unclear state.

## Sources

- [Radix Primitives](https://www.radix-ui.com/primitives/docs/overview/introduction)
- [Motion: `useReducedMotion`](https://motion.dev/docs/react-use-reduced-motion)
- [Utopia](https://utopia.fyi/)
- [GOV.UK Design System](https://design-system.service.gov.uk/)
