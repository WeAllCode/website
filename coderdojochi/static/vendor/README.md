# Vendored front-end libraries

Third-party files served from our own static bucket instead of a CDN. Refresh with `uv run invoke vendor`; bump versions in `vendor.json`.

- jQuery 3.8.0 — https://www.npmjs.com/package/jquery/v/3.8.0 — MIT
- Font Awesome Free 7.3.1 (SVGs) — https://www.npmjs.com/package/@fortawesome/fontawesome-free/v/7.3.1 — CC BY 4.0 (icons); only the SVGs the `{% icon %}` tag maps, in `fa-svgs/`, inlined by `coderdojochi/templatetags/icons.py`
- Font Awesome 4.7.0 — https://www.npmjs.com/package/font-awesome/v/4.7.0 — SIL OFL 1.1 (fonts), MIT (CSS); license section in `fontawesome4/README.md`
- Bootstrap 3.4.1 — https://www.npmjs.com/package/bootstrap/v/3.4.1 — MIT
- Chart.js 4.6.1 — https://www.npmjs.com/package/chart.js/v/4.6.1 — MIT
- Sentry browser SDK 11.12.0 — https://www.npmjs.com/package/@sentry/browser/v/11.12.0 — MIT; `bundle.min.js` comes from browser.sentry-cdn.com (the npm package has no browser bundles), pinned by sha384 in `vendor.json`
- Bungee (@fontsource/bungee) 5.3.0 — https://www.npmjs.com/package/@fontsource/bungee/v/5.3.0 — SIL OFL 1.1
- Poppins (@fontsource/poppins) 5.3.0 — https://www.npmjs.com/package/@fontsource/poppins/v/5.3.0 — SIL OFL 1.1
- Open Sans (@fontsource/open-sans) 5.3.0 — https://www.npmjs.com/package/@fontsource/open-sans/v/5.3.0 — SIL OFL 1.1
- Quicksand (@fontsource/quicksand) 5.3.0 — https://www.npmjs.com/package/@fontsource/quicksand/v/5.3.0 — SIL OFL 1.1

Transforms (applied by the task, flags in `vendor.json`): `strip_sourcemap` removes a `sourceMappingURL` comment when the `.map` isn't shipped; `drop_font_formats` removes `url()` entries for font formats we don't ship (SVG fonts, `.woff` fallbacks); `keep_subsets` keeps only the latin and latin-ext `@font-face` blocks. Django's manifest storage fails collectstatic on any missing `url()` or source-map reference, so the task checks every reference before writing.
