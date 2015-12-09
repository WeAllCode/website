'use strict';

var gulp = require('gulp');
var config = require('../config.json');

gulp.task('copy', function() {
    return gulp.src([
            config.img.src + '/**'
        ])
        .pipe(gulp.dest(config.img.dest));
});
