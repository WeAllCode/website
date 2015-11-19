'use strict';

var gulp = require('gulp'),
    config = require('../config.json'),
    del = require('del'),
    gutil = require('gulp-util');

gulp.task('clean', function() {
    del([
            config.css + '/*.css',
            config.img + '/sprites'
        ], function(err) {
            gutil.log(gutil.colors.magenta('CSS and sprites deleted for re-creation in a new build.'));
        });
});