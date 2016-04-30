'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var spritesmith = require('gulp.spritesmith');

var sassDest = config.sass.src + '/sprites';
var tmpl = config.sprites.src + '/spritesmith.template.mustache';
var padding = 5;

gulp.task('sprites', function() {
    var retinaGlobal = gulp.src(config.sprites.src + '/global-2x/*.png')
            .pipe(spritesmith({
                imgName: 'sprite-global@2x.png',
                cssName: '_sprites-global-2x.scss',
                cssTemplate: tmpl,
                cssOpts: {
                    sprite_type: 'global-2x'
                },
                padding: padding
            })),
        regularGlobal = gulp.src(config.sprites.src + '/global-1x/*.png')
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
    retinaGlobal.img.pipe(gulp.dest(config.sprites.dest));
    retinaGlobal.css.pipe(gulp.dest(sassDest));
    regularGlobal.img.pipe(gulp.dest(config.sprites.dest));
    regularGlobal.css.pipe(gulp.dest(sassDest));

});
