/**
 * Default task when Gulp is run for local development.
 */

'use strict';

var gulp = require('gulp'),
    runSequence = require('run-sequence');

// desktop js and all scss/images/etc
gulp.task('default', function(cb) {
    global.isWatching = true;

    runSequence(
        'clean',
        [
            'sprites',
            'sass'
        ],
        'watch',
        'browser-sync',
        'django',
        cb);
});
