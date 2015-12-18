'use strict';

var gulp = require('gulp');
var config = require('../config.json');

gulp.task('copy', function() {
    gulp.src([
        config.img.src + '/**'
    ])
      .pipe(gulp.dest(config.img.dest));

    gulp.src([
        config.css.src + '/**'
    ])
      .pipe(gulp.dest(config.css.dest));

    gulp.src([
        config.favico.src
    ])
      .pipe(gulp.dest(config.favico.dest));

    gulp.src([
        config.js.src + '/**'
    ])
      .pipe(gulp.dest(config.js.dest));
});
