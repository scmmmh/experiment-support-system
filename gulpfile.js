'use strict';

var gulp = require('gulp');
var sass = require('gulp-sass');
var concat = require('gulp-concat');
var babel = require('gulp-babel');
var modernizr = require('gulp-modernizr');
var uglify = require('gulp-uglify');
var pump = require('pump');

gulp.task('default', ['scss', 'js']);

// Task to build the CSS
gulp.task('scss', function(cb) {
    var count = 0;
    var pcb = function() {
        count++;
        if(count == 2) {
            cb();
        }
    }
    // Build the application CSS
    pump([gulp.src('src/static/scss/app.scss'),
          sass({
              includePaths: ['node_modules/foundation-sites/scss']
          }),
          gulp.src('src/static/scss/foundation-icons/foundation-icons.*'),
          uglify(),
          gulp.dest('src/ess/static/css')
    ], pcb);
    // Copy the font icons
    pump([gulp.src('src/static/scss/foundation-icons/svgs/*'),
          gulp.dest('src/ess/static/css/svgs')
    ], pcb);
});

// Task to build the JavaScript files
gulp.task('js', function(cb) {
    var count = 0;
    var pcb = function() {
        count++;
        if(count == 3) {
            cb();
        }
    }
    /* Build library files */
    pump([gulp.src(['node_modules/foundation-sites/js/foundation.core.js',
                    'node_modules/foundation-sites/js/foundation.util.*.js',
                    'node_modules/foundation-sites/js/foundation.abide.js',
                    'node_modules/foundation-sites/js/foundation.accordion.js',
                    'node_modules/foundation-sites/js/foundation.accordionMenu.js',
                    'node_modules/foundation-sites/js/foundation.drilldown.js',
                    'node_modules/foundation-sites/js/foundation.dropdown.js',
                    'node_modules/foundation-sites/js/foundation.dropdownMenu.js',
                    'node_modules/foundation-sites/js/foundation.equalizer.js',
                    'node_modules/foundation-sites/js/foundation.interchange.js',
                    'node_modules/foundation-sites/js/foundation.magellan.js',
                    'node_modules/foundation-sites/js/foundation.offcanvas.js',
                    'node_modules/foundation-sites/js/foundation.responsiveMenu.js',
                    'node_modules/foundation-sites/js/foundation.responsiveToggle.js',
                    'node_modules/foundation-sites/js/foundation.reveal.js',
                    'node_modules/foundation-sites/js/foundation.slider.js',
                    'node_modules/foundation-sites/js/foundation.sticky.js',
                    'node_modules/foundation-sites/js/foundation.tabs.js',
                    'node_modules/foundation-sites/js/foundation.toggler.js',
                    'node_modules/foundation-sites/js/foundation.tooltip.js',]),
          babel({
              presets: ['es2015']
          }),
          concat('foundation.js'),
          modernizr({
              options: ['html5shiv',
                        'html5printshiv',
                        'setClasses']
          }),
          gulp.src(['node_modules/jquery/dist/jquery.js',
                         'node_modules/what-input/what-input.js']),
          uglify(),
          gulp.dest('src/ess/static/js')
    ], pcb);
    /* Build frontend files */
    pump([gulp.src('src/static/js/frontend/*.js'),
          concat('frontend.js'),
          uglify(),
          gulp.dest('src/ess/static/js')
    ], pcb);
    /* Build backend files */
    pump([gulp.src('src/static/js/backend/*.js'),
          concat('backend.js'),
          uglify(),
          gulp.dest('src/ess/static/js')
    ], pcb);
});

// Task to watch the SCSS/JS files and re-build when needed
gulp.task('watch', function() {
    gulp.watch('src/static/scss/**/*.scss', ['scss']);
    gulp.watch('src/static/js/**/*.js', ['js']);
});
