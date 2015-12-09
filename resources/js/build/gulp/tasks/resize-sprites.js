'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var del = require('del');
var imageResize = require('gulp-image-resize');
var rename = require('gulp-rename');
var gutil = require('gulp-util');

gulp.task('resize-sprites', function() {
    del([config.sprites.dest + '/*-1x'], function(err) {
        gutil.log(gutil.colors.magenta('Removed prior *-1x folders for re-creation of new ones based on *-2x sprites.'));
    });

    gulp.src(config.sprites.src + '/*-2x/*.png')
        .pipe(imageResize({
            width: '50%',
            height: '50%'
        }))
        .pipe(rename(function(path) {
            path.dirname = path.dirname.substring(0, path.dirname.length - 3) + '-1x';
        }))
        .pipe(gulp.dest(config.sprites.dest));
});
