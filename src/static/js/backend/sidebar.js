(function($) {
    /**
     * The inlineEditor jQuery plugin provides the functionality for switching
     * between the preview and edit interface for a list of items.
     * 
     * {"reorder": "URL to use for submitting re-order data",
     *  "csrf_token": "CSRF token to include with any request"}
     */
    var methods = {
        init : function(options) {
            return this.each(function() {
                var sidebar = $(this);
                $(window).on('resize', function() {
                    sidebar.sidebar('update');
                }).on('scroll', function() {
                    sidebar.sidebar('update');
                });
            }).sidebar('update');
        },
        update: function() {
            var sidebar = $(this);
            var height = $(window).innerHeight();
            var header_height = 0;
            sidebar.parent().siblings('header').each(function() {
                header_height = header_height + $(this).outerHeight(true);
            });
            var scroll = $(window).scrollTop();
            if(scroll < header_height) {
                height = height - header_height + scroll;
                $('#sidebar').css('position', '').css('height', height + 'px');
            } else {
                $('#sidebar').css('position', 'fixed').css('top', '0px').css('height', height + 'px');
            }
        }
    };

    $.fn.sidebar = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' + method + ' does not exist on jQuery.sidebar');
        }
    };
}(jQuery));
