# Localization of Third-Party Assets - Implementation Guide

This document provides instructions for completing the localization of third-party hosted fonts and JavaScript files for the We All Code website.

## Overview

The following external CDN dependencies have been identified and template references have been updated to use local files:

### External Dependencies Localized:

1. **Font Awesome 5.8.2** (CSS + fonts)
   - Original: `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.8.2/css/all.min.css`
   - Local: `weallcode/static/weallcode/css/vendor/font-awesome.min.css`

2. **Font Awesome 4.6.3** (CSS + fonts) - used in admin templates
   - Original: `https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css`
   - Local: `weallcode/static/weallcode/css/vendor/font-awesome-4.6.3.min.css`

3. **Google Fonts** (CSS + font files)
   - Bungee, Poppins, Open Sans, Quicksand families
   - Original: Multiple Google Fonts URLs
   - Local: `weallcode/static/weallcode/css/vendor/google-fonts.css`

4. **jQuery 3.4.1**
   - Original: `https://cdnjs.cloudflare.com/ajax/libs/jquery/3.4.1/jquery.min.js`
   - Local: `weallcode/static/weallcode/js/vendor/jquery-3.4.1.min.js`

5. **jQuery 1.12.4** - used in admin templates
   - Original: `https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js`
   - Local: `weallcode/static/weallcode/js/vendor/jquery-1.12.4.min.js`

6. **What Input 5.2.1**
   - Original: `https://cdnjs.cloudflare.com/ajax/libs/what-input/5.2.1/what-input.min.js`
   - Local: `weallcode/static/weallcode/js/vendor/what-input.min.js`

7. **Foundation 6.5.1**
   - Original: `https://cdnjs.cloudflare.com/ajax/libs/foundation/6.5.1/js/foundation.min.js`
   - Local: `weallcode/static/weallcode/js/vendor/foundation.min.js`

8. **Bootstrap 3.3.7** (CSS + JS) - used in admin templates
   - Original: `https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css`
   - Local: `weallcode/static/weallcode/css/vendor/bootstrap-3.3.7.min.css`
   - Original: `https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js`
   - Local: `weallcode/static/weallcode/js/vendor/bootstrap-3.3.7.min.js`

9. **Seamless Scroll Polyfill 1.0.0**
   - Original: `https://cdn.jsdelivr.net/npm/seamless-scroll-polyfill@1.0.0/dist/es5/seamless.auto-polyfill.min.js`
   - Local: `weallcode/static/weallcode/js/vendor/seamless.auto-polyfill.min.js`

10. **JS Datepicker 5.18.0** (CSS + JS)
    - Original: `https://unpkg.com/js-datepicker@5.18.0/dist/datepicker.min.css`
    - Local: `weallcode/static/weallcode/css/vendor/datepicker.min.css`
    - Original: `https://unpkg.com/js-datepicker@5.18.0/dist/datepicker.min.js`
    - Local: `weallcode/static/weallcode/js/vendor/datepicker.min.js`

11. **HTML5 Shiv 3.7.3** & **Respond.js 1.4.2** - IE support
    - Original: `https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js`
    - Local: `weallcode/static/weallcode/js/vendor/html5shiv.min.js`
    - Original: `https://oss.maxcdn.com/respond/1.4.2/respond.min.js`
    - Local: `weallcode/static/weallcode/js/vendor/respond.min.js`

## External Dependencies Kept (Analytics/Tracking):

- Google Analytics (`https://www.google-analytics.com/analytics.js`)
- DonsPlus embed script (`https://embed.donsplus.com/...`)

These should remain external as they're tracking/analytics services that need to be hosted by the providers.

## Templates Updated:

1. `weallcode/templates/weallcode/_base.html` - Main base template
2. `coderdojochi/templates/welcome.html` - Welcome page with datepicker
3. `coderdojochi/templates/dashboard/_admin_base.html` - Admin base template

## Next Steps Required:

### 1. Download Actual Files

Replace all placeholder files in `weallcode/static/weallcode/css/vendor/` and `weallcode/static/weallcode/js/vendor/` with actual content from the URLs specified in the file headers.

### 2. Download Font Files

Download font files for:
- Font Awesome 5.8.2 icons (woff, woff2, etc.)
- Font Awesome 4.6.3 icons
- Google Fonts: Bungee, Poppins, Open Sans, Quicksand

Place in `weallcode/static/weallcode/fonts/` with appropriate subdirectories.

### 3. Update CSS Files

Update the CSS files to reference local font paths instead of external URLs:
- Update font-face declarations in `google-fonts.css`
- Update icon font paths in Font Awesome CSS files

### 4. Testing

Test the website thoroughly to ensure:
- All fonts load correctly
- All JavaScript functionality works
- Icons display properly
- No console errors about missing resources

## Directory Structure Created:

```
weallcode/static/weallcode/
├── css/
│   └── vendor/
│       ├── font-awesome.min.css
│       ├── font-awesome-4.6.3.min.css
│       ├── google-fonts.css
│       ├── bootstrap-3.3.7.min.css
│       └── datepicker.min.css
├── js/
│   └── vendor/
│       ├── jquery-3.4.1.min.js
│       ├── jquery-1.12.4.min.js
│       ├── what-input.min.js
│       ├── foundation.min.js
│       ├── bootstrap-3.3.7.min.js
│       ├── seamless.auto-polyfill.min.js
│       ├── datepicker.min.js
│       ├── html5shiv.min.js
│       └── respond.min.js
└── fonts/
    └── README.md (with font download instructions)
```

## Commands to Download Files:

Use these commands or equivalent tools to download the actual files:

```bash
# CSS Files
curl -o weallcode/static/weallcode/css/vendor/font-awesome.min.css "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.8.2/css/all.min.css"
curl -o weallcode/static/weallcode/css/vendor/font-awesome-4.6.3.min.css "https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css"
curl -o weallcode/static/weallcode/css/vendor/bootstrap-3.3.7.min.css "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"
curl -o weallcode/static/weallcode/css/vendor/datepicker.min.css "https://unpkg.com/js-datepicker@5.18.0/dist/datepicker.min.css"

# JavaScript Files
curl -o weallcode/static/weallcode/js/vendor/jquery-3.4.1.min.js "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.4.1/jquery.min.js"
curl -o weallcode/static/weallcode/js/vendor/jquery-1.12.4.min.js "https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"
curl -o weallcode/static/weallcode/js/vendor/what-input.min.js "https://cdnjs.cloudflare.com/ajax/libs/what-input/5.2.1/what-input.min.js"
curl -o weallcode/static/weallcode/js/vendor/foundation.min.js "https://cdnjs.cloudflare.com/ajax/libs/foundation/6.5.1/js/foundation.min.js"
curl -o weallcode/static/weallcode/js/vendor/bootstrap-3.3.7.min.js "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"
curl -o weallcode/static/weallcode/js/vendor/seamless.auto-polyfill.min.js "https://cdn.jsdelivr.net/npm/seamless-scroll-polyfill@1.0.0/dist/es5/seamless.auto-polyfill.min.js"
curl -o weallcode/static/weallcode/js/vendor/datepicker.min.js "https://unpkg.com/js-datepicker@5.18.0/dist/datepicker.min.js"
curl -o weallcode/static/weallcode/js/vendor/html5shiv.min.js "https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"
curl -o weallcode/static/weallcode/js/vendor/respond.min.js "https://oss.maxcdn.com/respond/1.4.2/respond.min.js"
```

For Google Fonts, use https://google-webfonts-helper.herokuapp.com/ to download the font files and generate the CSS with local references.