/**
 * This task requires the following software to be installed:
 *
 * ImageAlpha (FREE: http://pngmini.com/)
 * ImageOptim (FREE: https://imageoptim.com/)
 * JPEGmini ($20: http://www.jpegmini.com/)
 */

'use strict';

var gulp = require('gulp'),
    config = require('../config.json'),
    shell = require('gulp-shell');

gulp.task('imagemin', shell.task([
    'imageoptim -d ' + config.img + ' -a -j -q'
]));