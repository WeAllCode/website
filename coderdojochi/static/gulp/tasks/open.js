'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var open = require('gulp-open');

gulp.task('open', function() {
    // a valid file is necessary for gulp.src or the task will be overlooked and it won't open
    gulp.src(config.js.src + '/cdc.js')
        .pipe(open('', {url: 'http://localhost:3000'}));
});
