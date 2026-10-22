# Rendered UI quality checklist

Do not declare interface work complete from source inspection alone.

## Viewports

Inspect representative rendered widths, including:

- 320 px narrow mobile;
- 375–390 px common mobile;
- 768 px tablet or narrow split view;
- 1024 px compact desktop;
- 1280–1440 px standard desktop;
- a wide viewport that reveals uncontrolled line length or empty space.

Also drag continuously between sizes and test zoom. Device presets are samples,
not coverage.

## Content and state stress tests

- shortest and longest realistic titles, labels, names, and translated copy;
- zero, negative, very large, and rapidly changing numeric values;
- missing, portrait, landscape, and unusually tall media;
- loading, skeleton, empty, partial, error, success, disabled, selected, and
  permission-denied states;
- slow network and delayed interaction feedback;
- destructive actions and recovery paths.

## Interaction

- keyboard-only traversal and logical focus order;
- visible focus, hover, pressed, selected, disabled, validation, and busy states;
- touch targets and spacing on mobile;
- dialogs, menus, tooltips, sticky regions, browser back, and deep links;
- on-screen keyboard overlap;
- reduced-motion behavior.

## Visual integrity

- no accidental horizontal page scrolling;
- no clipped text, controls, focus rings, menus, or tooltips;
- no unexpected layout shift;
- consistent alignment anchors, grid spans, radii, borders, and shadows;
- readable measure, line height, contrast, and wrapping;
- clear primary action and hierarchy;
- no decorative controls, meaningless cards, or repeated emphasis;
- Russian punctuation and nonbreaking relationships reviewed when applicable.

## Completion evidence

Capture screenshots at key widths, compare them to the intended hierarchy, and
record any intentional deviations. When code is available, run the project's
tests, lint, and accessibility checks in addition to the visual pass.

The work is complete only when critical flows remain understandable and
operable across the tested widths, input modes, states, and content extremes.
