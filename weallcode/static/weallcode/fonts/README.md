# Font Files

This directory should contain the locally hosted font files for the following fonts:

## Google Fonts Required:
1. **Bungee** (regular weight)
2. **Poppins** (multiple weights as needed)
3. **Open Sans** (300, 400, 700 weights)
4. **Quicksand** (300, 400, 700 weights)

## Font Awesome Icons:
Font Awesome 5.8.2 icon fonts (woff, woff2, etc.)

## Directory Structure:
```
fonts/
├── google-fonts/
│   ├── bungee/
│   ├── poppins/
│   ├── open-sans/
│   └── quicksand/
└── fontawesome/
    └── (Font Awesome font files)
```

## How to Obtain:
1. For Google Fonts: Use https://google-webfonts-helper.herokuapp.com/fonts
2. For Font Awesome: Download from official FontAwesome releases

The CSS files in `/css/vendor/` need to be updated to reference these local font files.