'use strict';

var gulp = require('gulp');
var sass = require('gulp-sass');
var concat = require('gulp-concat');
var babel = require('gulp-babel');

gulp.task('default', ['scss', 'js']);

// Task to build the CSS
gulp.task('scss', function() {
    // Build the application CSS
    gulp.src('src/static/scss/app.scss').
        pipe(sass({
            includePaths: ['node_modules/foundation-sites/scss']
        })).
        pipe(gulp.dest('src/ess/static/css'));
    // Copy the font icons
    gulp.src('src/static/scss/foundation-icons/svgs/*').
        pipe(gulp.dest('src/ess/static/css/svgs'));
    gulp.src('src/static/scss/foundation-icons/foundation-icons.*').
        pipe(gulp.dest('src/ess/static/css'));
});

// Task to build the JavaScript files
gulp.task('js', function() {
    gulp.src(['node_modules/jquery/dist/jquery.js',
              'node_modules/what-input/what-input.js']).
        pipe(gulp.dest('src/ess/static/js'));
    gulp.src(['node_modules/foundation-sites/js/foundation.core.js',
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
              'node_modules/foundation-sites/js/foundation.tooltip.js',]).
        pipe(babel({
            presets: ['es2015']
        })).
        pipe(concat('foundation.js')).
        pipe(gulp.dest('src/ess/static/js'));
    gulp.src('src/static/js/*.js').
        pipe(concat('app.js')).
        pipe(gulp.dest('src/ess/static/js'));
});

// Task to watch the SCSS/JS files and re-build when needed
gulp.task('watch', function() {
    gulp.watch('src/static/scss/**/*.scss', ['scss']);
    gulp.watch('src/static/js/*.js', ['js']);
});
