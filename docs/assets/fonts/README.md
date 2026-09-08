# Self-hosted fonts

RED THREADS serves these fonts locally. They are original, unmodified TTF files from the official [Google Fonts repository](https://github.com/google/fonts/tree/5e35378e6bda803962ee6fd257e444a7d459660d), downloaded on 2026-09-08. No font service is contacted at runtime.

| Font | Use | Version | Weight | Size | Source | License notice |
| --- | --- | --- | --- | --- | --- | --- |
| Bebas Neue Regular | Display lettering | 2.000 | 400 | 61,400 bytes | [Original TTF](https://github.com/google/fonts/blob/5e35378e6bda803962ee6fd257e444a7d459660d/ofl/bebasneue/BebasNeue-Regular.ttf) | [OFL-Bebas-Neue.txt](OFL-Bebas-Neue.txt) |
| Barlow Condensed SemiBold | Headings | 1.408 | 600 | 109,428 bytes | [Original TTF](https://github.com/google/fonts/blob/5e35378e6bda803962ee6fd257e444a7d459660d/ofl/barlowcondensed/BarlowCondensed-SemiBold.ttf) | [OFL-Barlow-Condensed.txt](OFL-Barlow-Condensed.txt) |

Both families use the SIL Open Font License 1.1. The full upstream copyright and license notices accompany the fonts with their wording preserved (line endings and trailing whitespace normalized), from [Bebas Neue's OFL.txt](https://github.com/google/fonts/blob/5e35378e6bda803962ee6fd257e444a7d459660d/ofl/bebasneue/OFL.txt) and [Barlow Condensed's OFL.txt](https://github.com/google/fonts/blob/5e35378e6bda803962ee6fd257e444a7d459660d/ofl/barlowcondensed/OFL.txt). Font metadata, names, glyphs, and embedded copyright notices are preserved. These font licenses remain separate from the surrounding project's license.

The TTF files retain the upstream character coverage. No local font installation, external stylesheet, or conversion is required. For CSS in `docs/assets/site.css`, use:

```css
@font-face {
  font-family: "Bebas Neue";
  src: url("./fonts/BebasNeue-Regular.ttf") format("truetype");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}

@font-face {
  font-family: "Barlow Condensed";
  src: url("./fonts/BarlowCondensed-SemiBold.ttf") format("truetype");
  font-style: normal;
  font-weight: 600;
  font-display: swap;
}
```
