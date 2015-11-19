'use strict';

var gulp = require('gulp'),
    config = require('../config.json'),
    spritesmith = require('gulp.spritesmith');

var spriteSrc = config.dev + config.sprites,
    spriteDest = config.img + '/' + config.sprites,
    sassDest = config.sass + '/' + config.sprites,
    tmpl = spriteSrc + '/spritesmith.template.mustache',
    padding = 5;

gulp.task('sprites', function() {
    var retinaGlobal = gulp.src(spriteSrc + '/global-2x/*.png')
            .pipe(spritesmith({
                imgName: 'sprite-global@2x.png',
                cssName: '_sprites-global-2x.scss',
                cssTemplate: tmpl,
                cssOpts: {
                    sprite_type: 'global-2x'
                },
                padding: padding
            })),
        regularGlobal = gulp.src(spriteSrc + '/global-1x/*.png')
            .pipe(spritesmith({
                imgName: 'sprite-global.png',
                cssName: '_sprites-global.scss',
                cssTemplate: tmpl,
                cssOpts: {
                    sprite_type: 'global'
                },
                padding: padding
            }));

    // generate global sprites and sass
    retinaGlobal.img.pipe(gulp.dest(spriteDest));
    retinaGlobal.css.pipe(gulp.dest(sassDest));
    regularGlobal.img.pipe(gulp.dest(spriteDest));
    regularGlobal.css.pipe(gulp.dest(sassDest));

});