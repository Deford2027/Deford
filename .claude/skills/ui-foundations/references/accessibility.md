# Interface accessibility

Accessibility is a design input, not a finishing pass.

## Semantics and keyboard

- Use native landmarks, headings, links, buttons, labels, inputs, tables, and
  dialogs before recreating them with generic containers and ARIA.
- Keep the DOM and keyboard order aligned with the visual reading order.
- Every interactive element must be reachable and operable by keyboard.
- Provide a visible focus indicator with adequate contrast; do not remove the
  outline without an equivalent replacement.
- Manage focus when opening and closing dialogs, navigating client-side, or
  inserting a blocking error.

## Names, instructions, and errors

- Every control needs an accessible name that describes its action or input.
- Placeholder text is not a label.
- Associate help and error text with the relevant field. State what happened and
  how to recover.
- Do not encode state, severity, or validity by color alone.
- Announce important asynchronous status changes without interrupting ordinary
  reading.

## Perception

- Meet WCAG AA contrast: generally 4.5:1 for normal text and 3:1 for large text;
  verify non-text contrast for essential controls and focus states.
- Provide meaningful alternative text for informative images. Use empty alt text
  for decoration.
- Captions, transcripts, or equivalent alternatives are required for relevant
  audio and video.
- Content must survive text enlargement, zoom, and custom user settings.

## Motion

- Honor `prefers-reduced-motion`.
- Remove or replace large spatial movement, parallax, autoplay, and repeated
  ambient motion when reduced motion is requested.
- Keep necessary feedback immediate and understandable without motion.
- Do not flash content in ways that can trigger seizures.

## Verification

Test with keyboard only, browser zoom, reduced-motion settings, automated
accessibility tooling, and at least a basic screen-reader pass for critical
flows. Automated checks do not replace interaction testing.

## Sources

- [W3C Web Content Accessibility Guidelines](https://www.w3.org/WAI/standards-guidelines/wcag/)
- [W3C: Understanding Reflow](https://www.w3.org/WAI/WCAG21/Understanding/reflow)
- [W3C: Target Size (Enhanced)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced)
