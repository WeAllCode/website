'use strict';

var gulp = require('gulp'),
    config = require('../config.json'),
    gulpif = require('gulp-if'),
    sass = require('gulp-sass'),
    sourcemaps = require('gulp-sourcemaps'),
    autoprefixer = require('gulp-autoprefixer'),
    browserSync = require('browser-sync'),
    handleErrors = require('../utils/handle-errors');

gulp.task('sass', function() {
    return gulp.src(config.sass + '/*.scss')
        .pipe(gulpif(global.isWatching, sourcemaps.init()))
        .pipe(sass())
        .pipe(autoprefixer({
            browsers: ['Firefox > 25', 'last 4 versions', '> 3%', 'ie 8']
        }))
        .pipe(gulpif(global.isWatching, sourcemaps.write()))
        .on('error', handleErrors)
        .pipe(gulp.dest(config.css))
        .pipe(gulpif(global.isWatching, browserSync.reload({stream: true})));
});