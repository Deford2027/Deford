# Responsive and mobile design

## Design transformations, not scaled screenshots

Start with the narrowest meaningful layout when practical. Preserve task
priority, but change the composition when available space changes:

- columns may stack or become independently scrollable;
- secondary information may move behind disclosure;
- dense tables may become prioritized rows, cards, or a labelled scroller;
- navigation may change pattern rather than merely shrink;
- action groups may wrap, stack, or become a stable action region;
- imagery may crop differently or disappear only when it carries no essential
  information.

Never hide essential functionality simply because the screen is narrow.

## Breakpoints

- Add a breakpoint where the current composition fails: text becomes
  unreadable, controls collide, a measure becomes too wide, or hierarchy breaks.
- Prefer intrinsic layout and a small number of content-driven breakpoints.
- Use container queries for components embedded in multiple shell widths.
- Test between common device widths; defects often appear between presets.

## Reflow and zoom

- Include the viewport meta tag.
- At 320 CSS px wide, ordinary content should reflow without horizontal page
  scrolling or loss of information. Two-dimensional content such as a complex
  data table may use an internal, labelled scroller.
- Test browser zoom to 200% and WCAG reflow conditions approximating 400%.
- Do not disable pinch zoom or user scaling.
- Avoid fixed heights on text containers and fixed widths on controls with
  localized labels.

## Touch, keyboards, and device edges

- Aim for at least 44 by 44 CSS px for primary touch controls. WCAG 2.2 minimum
  target sizing has contextual exceptions, but larger targets are safer.
- Keep sufficient separation between adjacent destructive or irreversible
  actions.
- Use at least 16 CSS px for mobile form input text.
- Respect safe-area insets for edge-to-edge mobile layouts.
- Ensure fixed action bars do not cover content or the on-screen keyboard.
- Make all functionality available without hover and in both portrait and
  landscape when the product supports them.

## Performance and media

- Provide responsive image sources and correct intrinsic dimensions.
- Prioritize the above-the-fold media that affects perceived load; lazy-load
  offscreen media.
- Reserve layout space to prevent shifting.
- Avoid heavyweight motion or large background video on constrained devices
  unless it is essential and has a fallback.

## Sources

- [MDN: Responsive design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design)
- [MDN: Media queries](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Media_queries)
- [A List Apart: Responsive Web Design](https://alistapart.com/article/responsive-web-design/)
- [W3C: Understanding Reflow](https://www.w3.org/WAI/WCAG21/Understanding/reflow)
- [W3C: Target Size (Enhanced)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced)
