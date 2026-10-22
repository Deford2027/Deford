# Typography

## Establish roles before sizes

Define a small set of semantic roles: display, page title, section title, body,
compact UI, label, caption, code, and numeric data. Each role needs an explicit
font family, real available weight, size, line height, letter spacing, and
wrapping policy.

- Use no more type families than the product can justify and load efficiently.
- Verify that every font contains the scripts, punctuation, currency signs, and
  numeral styles the content needs. Never rely on accidental fallback for
  Cyrillic.
- Do not synthesize weights or italics when a real face is available.
- Use a restrained modular or fluid scale. Adjacent levels must be visibly
  distinct without requiring many nearly identical sizes.
- Use unitless line heights for scalable text. Dense UI labels can be tighter;
  multi-line prose needs more air.

## Readability

- Keep ordinary long-form lines roughly 45–75 characters; approximately
  60–75 is a useful default for continuous reading. UI text is usually shorter.
- Body copy should not be justified unless language-aware hyphenation and
  editorial control make its spacing reliable.
- Avoid all caps for sentences. Use it sparingly for short labels and add
  tracking only when the chosen font needs it.
- Use `font-variant-numeric: tabular-nums` for columns of changing numbers,
  timers, dashboards, and financial tables; use proportional numerals in prose.
- Use `text-wrap: balance` for short headings and `text-wrap: pretty` where
  supported for prose, with sensible fallbacks.
- Avoid tiny text as a way to fit more information. Reduce density by editing,
  grouping, disclosure, or responsive transformation.

## Responsive type

- Prefer a bounded fluid formula such as `clamp(min, fluid, max)` for display
  sizes and large spacing. Test the values between bounds; a formula is not a
  substitute for visual review.
- Do not define essential text solely in viewport units because it can defeat
  browser zoom.
- On mobile web, keep form inputs at least 16 CSS px to avoid unwanted iOS zoom.
- Verify 200% zoom and reflow at an equivalent narrow viewport. Text must not
  overlap, clip, or require two-dimensional scrolling.

## Punctuation and details

- Use real typographic characters when the language requires them: correct
  quotation marks, apostrophes, dashes, ellipses, multiplication signs, minus
  signs, and nonbreaking spaces.
- Avoid forced line breaks in dynamic copy. Let the container and wrapping
  policy do the work.
- Do not convert source text mechanically without preserving meaning, URLs,
  code, identifiers, and user-entered data.

## Sources

- [Apple Human Interface Guidelines: Typography](https://developer.apple.com/design/human-interface-guidelines/typography)
- [Practical Typography: Summary of key rules](https://practicaltypography.com/summary-of-key-rules.html)
- [Thinking with Type](https://ellenlupton.com/Thinking-with-Type)
- [Utopia fluid type calculator](https://utopia.fyi/)
