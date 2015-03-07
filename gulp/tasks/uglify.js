var gulp = require('gulp'),
	config = require('../config.json'),
	rename = require('gulp-rename'),
	uglify = require('gulp-uglify');
 
gulp.task('uglify', function() {
  gulp.src(config.js + '/cdc.js')
  	.pipe(rename('cdc.min.js'))
    .pipe(uglify())
    .pipe(gulp.dest(config.js))
});