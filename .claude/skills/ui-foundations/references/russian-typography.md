# Russian and Cyrillic typography

Apply these rules to authored Russian copy. Preserve intentional brand spelling,
legal forms, code, URLs, identifiers, and verbatim user data.

## Punctuation

- Use Russian outer quotation marks: `«ёлочки»`.
- Use `„лапки“` for a quotation nested inside Russian quotation marks when the
  editorial style calls for it.
- Use a long sentence dash with surrounding spaces according to the chosen
  editorial style. Use an en dash for numeric or date ranges, a hyphen inside
  compound words, and the mathematical minus sign `−` for negative values.
- Use the ellipsis character `…` rather than three full stops in edited prose.
- Do not mix visually similar Latin and Cyrillic letters.

## Nonbreaking relationships

Keep tightly related tokens together when a break would harm comprehension:

- initials with a surname;
- a number with its unit, currency, percent sign, or abbreviated noun;
- `№` with the following number;
- short date and time expressions where a split would be awkward;
- short prepositions or conjunctions with the following word when the layout
  genuinely benefits.

Do not flood text with nonbreaking spaces. Excessive binding causes large gaps
and overflow on narrow screens.

## Numbers, units, and dates

- Use a consistent locale-aware thousands separator and decimal separator.
- Keep a space between a number and most units or currencies when prescribed by
  the style: `25 км`, `12 %`, `5 000 ₽`.
- Use tabular numerals for comparable dashboard values and proportional numerals
  in sentences.
- Choose one date and time convention for the product and make ambiguous
  machine-oriented formats human-readable at the presentation layer.

## Line endings and copy quality

- Avoid single short words stranded at the end of a heading when a natural edit
  or balanced wrap can fix it.
- Never insert manual `<br>` tags into dynamic headings solely to match one
  screenshot.
- Check the exact mobile rendering: Russian words are often longer than English
  labels, and inflected phrases expand controls.
- Use automated typography as an editorial aid, then review the result. It must
  not rewrite code, links, tracking values, or structured data.

## Sources

- [Бюро Горбунова: «Типографика и вёрстка»](https://bureau.ru/projects/book-typography/)
- [Ководство: экранная типографика](https://www.artlebedev.ru/kovodstvo/sections/62/)
- [Типограф студии Артемия Лебедева](https://www.artlebedev.ru/typograf/about/)
