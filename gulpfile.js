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
gulp.task('scss', ['scss-backend', 'scss-frontend', 'material-design-icons']);
gulp.task('js', ['library-js', 'frontend-js', 'backend-js']);
gulp.task('library-js', ['what-input', 'modernizr', 'jquery', 'jquery-ui', 'foundation-js', 'chart-js']);

gulp.task('scss-backend', function(cb) {
    var css_sources = ['src/static/scss/base-settings.scss'];
    css_sources.push('src/static/scss/foundation-loader.scss');
    css_sources.push('src/static/scss/backend.scss');
    pump([
        gulp.src(css_sources, {base: 'src/static/scss'}),
        concat('backend.scss'),
        sass({
            includePaths: ['node_modules/foundation-sites/scss',
                           'node_modules/foundation-icons']
        }),
        clean_css(),
        rename('backend.min.css'),
        gulp.dest('src/ess/static/css')
    ], cb);
});

gulp.task('scss-frontend', function(cb) {
    var css_sources = ['src/static/scss/base-settings.scss'];
    css_sources.push('src/static/scss/foundation-loader.scss');
    css_sources.push('src/static/scss/frontend.scss');
    pump([
        gulp.src(css_sources, {base: 'src/static/scss'}),
        concat('frontend.scss'),
        sass({
            includePaths: ['node_modules/foundation-sites/scss',
                           'node_modules/foundation-icons']
        }),
        clean_css(),
        rename('frontend.min.css'),
        gulp.dest('src/ess/static/css')
    ], cb);
});

gulp.task('material-design-icons', function(cb) {
    pump([
        gulp.src([
            'node_modules/material-design-icons/iconfont/*.eot',
            'node_modules/material-design-icons/iconfont/*.svg',
            'node_modules/material-design-icons/iconfont/*.ttf',
            'node_modules/material-design-icons/iconfont/*.woff',
            'node_modules/material-design-icons/iconfont/*.woff2'],
            {base: 'node_modules/material-design-icons/iconfont'}),
        gulp.dest('src/ess/static/css')
    ], cb);
});

gulp.task('foundation-js', function(cb) {
    pump([
        gulp.src([
            'node_modules/foundation-sites/js/foundation.core.js',
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
            'node_modules/foundation-sites/js/foundation.tooltip.js'
        ]),
        babel({
            presets: ['es2015']
        }),
        concat('foundation.js'),
        uglify(),
        gulp.dest('src/ess/static/js')
    ], cb);
});

gulp.task('modernizr', function(cb) {
    pump([
        modernizr({
            options: [
                'html5shiv',
                'html5printshiv',
                'setClasses']
        }),
        uglify(),
        gulp.dest('src/ess/static/js')
    ], cb);
});

gulp.task('jquery', function(cb) {
    pump([
        gulp.src([
            'node_modules/jquery/dist/jquery.js',
        ]),
        uglify(),
        gulp.dest('src/ess/static/js')
    ], cb);
});

gulp.task('what-input', function(cb) {
    pump([
        gulp.src([
            'node_modules/what-input/dist/what-input.js'
        ]),
        uglify(),
        gulp.dest('src/ess/static/js')
    ], cb);
});

gulp.task('jquery-ui', function(cb) {
    pump([
        gulp.src([
            'node_modules/jquery-ui/ui/version.js',
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
            'node_modules/jquery-ui/ui/widgets/sortable.js'
        ]),
        concat('jquery-ui.js'),
        uglify(),
        gulp.dest('src/ess/static/js')
    ], cb);
});

gulp.task('chart-js', function(cb) {
    pump([
       gulp.src([
           'src/static/js/pallette.js',
           'node_modules/chart.js/dist/Chart.bundle.js'
       ]),
       concat('chart.js'),
       uglify(),
       gulp.dest('src/ess/static/js')
    ], cb);
});

gulp.task('frontend-js', function(cb) {
    pump([
        gulp.src('src/static/js/frontend/*.js'),
        concat('frontend.js'),
        uglify(),
        gulp.dest('src/ess/static/js')
    ], cb);
});

gulp.task('backend-js', function(cb) {
    pump([
        gulp.src('src/static/js/backend/*.js'),
        concat('backend.js'),
        uglify(),
        gulp.dest('src/ess/static/js')
    ], cb);
});

// Task to watch the SCSS/JS files and re-build when needed
gulp.task('watch', function() {
    gulp.watch('src/static/scss/**/*.scss', ['scss-backend', 'scss-frontend']);
    gulp.watch('src/static/js/**/*.js', ['frontend-js', 'backend-js']);
});
