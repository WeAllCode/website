'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var rename = require('gulp-rename');
var uglify = require('gulp-uglify');

gulp.task('uglify', function() {
  gulp.src(config.js.src + '/cdc.js')
  	.pipe(rename('cdc.min.js'))
    .pipe(uglify())
    .pipe(gulp.dest(config.js.dest))
});
