/**
 * Default task when Gulp is run for local development.
 */

'use strict';

var gulp = require('gulp');
var runSequence = require('run-sequence');

// desktop js and all scss/images/etc
gulp.task('default', function(cb) {
    global.isWatching = true;

    runSequence(
        [
            'sprites',
            'sass'
        ],
        cb);
});
