'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var browserSync = require('browser-sync');

gulp.task('browser-sync', function() {
    browserSync({
        proxy: 'localhost:8000',
        logPrefix: 'CoderDojoChi',
        open: false,
        notify: false
    });
});
