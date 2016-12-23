'use strict';

var gulp = require('gulp');
var sass = require('gulp-sass');
var concat = require('gulp-concat');
var clean_css = require('gulp-clean-css');
var rename = require('gulp-rename');
var babel = require('gulp-babel');
var modernizr = require('gulp-modernizr');
var uglify = require('gulp-uglify');
var pump = require('pump');

gulp.task('default', ['scss', 'js']);

// Task to build the CSS
gulp.task('scss', function(cb) {
    // Build the CSS
    var css_sources = ['src/static/scss/base-settings.scss'];
    css_sources.push('src/static/scss/foundation-loader.scss');
    css_sources.push('src/static/scss/application.scss');
    gulp.src(css_sources, {base: 'src/static/scss'}).
        pipe(concat('application.scss')).
        pipe(sass({
            includePaths: ['node_modules/foundation-sites/scss',
                           'node_modules/foundation-icons']
        })).
        pipe(clean_css()).
        pipe(rename('application.min.css')).
        pipe(gulp.dest('src/ess/static/css'));
    // Copy Material Design Icon Fonts
    gulp.src(['node_modules/material-design-icons/iconfont/*.eot',
              'node_modules/material-design-icons/iconfont/*.svg',
              'node_modules/material-design-icons/iconfont/*.ttf',
              'node_modules/material-design-icons/iconfont/*.woff',
              'node_modules/material-design-icons/iconfont/*.woff2'], {base: 'node_modules/material-design-icons/iconfont'}).
        pipe(gulp.dest('src/ess/static/css'));
});

// Task to build the JavaScript files
gulp.task('js', function(cb) {
    var count = 0;
    var pcb = function() {
        count++;
        if(count == 5) {
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
          uglify(),
          gulp.dest('src/ess/static/js')
    ], pcb);
    pump([modernizr({
              options: ['html5shiv',
                        'html5printshiv',
                        'setClasses']
          }),
          gulp.src(['node_modules/jquery/dist/jquery.js',
                    'node_modules/what-input/what-input.js']),
          uglify(),
          gulp.dest('src/ess/static/js')
    ], pcb);
    pump([gulp.src(['node_modules/jquery-ui/ui/version.js',
                    'node_modules/jquery-ui/ui/effect.js',
                    'node_modules/jquery-ui/ui/plugin.js',
                    'node_modules/jquery-ui/ui/widget.js',
                    'node_modules/jquery-ui/ui/position.js',
                    'node_modules/jquery-ui/ui/data.js',
                    'node_modules/jquery-ui/ui/safe-active-element.js',
                    'node_modules/jquery-ui/ui/safe-blur.js',
                    'node_modules/jquery-ui/ui/disable-selection.js',
                    'node_modules/jquery-ui/ui/scroll-parent.js',
                    'node_modules/jquery-ui/ui/widgets/mouse.js',
                    'node_modules/jquery-ui/ui/widgets/draggable.js',
                    'node_modules/jquery-ui/ui/widgets/dropable.js',
                    'node_modules/jquery-ui/ui/widgets/sortable.js']),
          concat('jquery-ui.js'),
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
