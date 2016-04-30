'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var del = require('del');
var gutil = require('gulp-util');

gulp.task('clean', function() {
    del([
            config.css.dest + '/*.css',
            config.sprites.dest
        ], function(err) {
            gutil.log(gutil.colors.magenta('CSS and sprites deleted for re-creation in a new build.'));
        });
});
