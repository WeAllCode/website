'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var gulpif = require('gulp-if');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var autoprefixer = require('gulp-autoprefixer');
var handleErrors = require('../utils/handle-errors');

gulp.task('sass', function() {

    return gulp.src(config.sass.src + '/*.scss')
        .pipe(gulpif(global.isWatching, sourcemaps.init()))
        .pipe(sass({
            outputStyle: "expanded",
        }))
        .pipe(autoprefixer({
            browsers: ['Firefox > 25', 'last 4 versions', '> 3%', 'ie 8']
        }))
        .pipe(gulpif(global.isWatching, sourcemaps.write()))
        .on('error', handleErrors)
        .pipe(gulp.dest(config.sass.dest))
});
