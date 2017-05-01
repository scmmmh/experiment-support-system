(function($) {
    /**
     * Select a sub-set of the given palette of colours.
     * 
     * @param pal The palette to select from
     * @param indexes The indexes in the palette to select
     * @returns The selected sub-set of the palette
     */
    function sub_palette(pal, indexes) {
        var result = [];
        for(var idx = 0; idx < indexes.length; idx++) {
            if(indexes[idx] >= 0 && indexes[idx] < pal.length) {
                result.push(pal[indexes[idx]]);
            }
        }
        return result;
    }
    function fix_colors(colors) {
        for(var idx = 0; idx < colors.length; idx++) {
            if(colors[idx][0] != '#') {
                colors[idx] = '#' + colors[idx];
            }
        }
        return colors;
    }
    /**
     * The chart jQuery plugin constructs a new chart.js chart for the given element
     * (which must be a <canvas>).
     */
    var methods = {
        init : function(options) {
            return this.each(function() {
                var component = $(this);
                var data = {};
                if(component.data('chart-labels')) {
                    data['labels'] = component.data('chart-labels');
                }
                if(component.data('chart-data')) {
                    var dataset = {
                        data: component.data('chart-data')
                    };
                    if(component.data('chart-title')) {
                        dataset['label'] = component.data('chart-title');
                    }
                    if(component.data('chart-colors')) {
                        dataset['backgroundColor'] = component.data('chart-colors');
                    } else if(component.data('chart-color-idxs') && options.colors) {
                        dataset['backgroundColor'] = fix_colors(sub_palette(options.colors, component.data('chart-color-idxs')));
                    } else {
                        dataset['backgroundColor'] = fix_colors(palette(['qualitative'], component.data('chart-data').length));
                    }
                    data['datasets'] = [dataset];
                }
                var chart_options = {
                    legend: {
                        display: !component.data('chart-hide-legend')
                    }
                };
                if(component.data('chart-type') == 'horizontalBar') {
                    chart_options.scales = {
                        xAxes: [{ticks: {beginAtZero: true}}],
                        yAxes: [{ticks: {mirror: true}}]
                    };
                }
                new Chart(component, {
                    type: component.data('chart-type'),
                    data: data,
                    options: chart_options
                });
            });
        }
    };

    $.fn.chart = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' + method + ' does not exist on jQuery.chart');
        }
    };
}(jQuery));
