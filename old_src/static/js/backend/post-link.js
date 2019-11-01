(function($) {
    /**
     * The postLink jQuery plugin provides automatic submission of a standard
     * link via a POST request. If a data-ess-confirm attribute is present on
     * the link, then the user has to confirm the action. The data-ess-confirm
     * attribute should look like this:
     * 
     * {"title": "Title string", "msg": "Main message string", "cancel":
     * {"label": "Cancel button label string", "class": "CSS classes"}, "ok":
     * {"label": "Ok button label string", "class": "CSS classes"}}
     */
    var methods = {
        init : function(options) {
            return this.each(function() {
                var component = $(this);
                component.on('click', function(ev) {
                    ev.preventDefault();
                    var confirm = component.data('ess-confirm');
                    if (confirm) {
                        var html = '<div id="confirm-modal" class="reveal" data-reveal="">'
                                + '<h2>' + (confirm.title || 'Please confirm')
                                + '</h2>' + '<p>' + confirm.msg + '</p>'
                                + '<div class="text-right">';
                        if (confirm.cancel) {
                            html = html + '<a href="#" class="button cancel '
                                    + (confirm.cancel.class_ || '') + '">'
                                    + (confirm.cancel.label || 'Cancel')
                                    + '</a>&nbsp;';
                        }
                        if (confirm.ok) {
                            html = html + '<a href="#" class="button ok '
                                    + (confirm.ok.class_ || '') + '">'
                                    + (confirm.ok.label || 'Ok') + '</a>';
                        }
                        html = html + '</div>' + '</div>';
                        var dlg = $(html);
                        $('body').append(dlg);
                        var reveal = new Foundation.Reveal(dlg);
                        dlg.find('a.cancel').on('click', function(ev) {
                            ev.preventDefault();
                            reveal.close();
                        });
                        dlg.find('a.ok').on('click', function(ev) {
                            ev.preventDefault();
                            var frm = $('<form action="'
                                    + component.attr('href')
                                    + '" method="post"></form>');
                            $('body').append(frm);
                            frm.submit();
                        });
                        $(document).on('closed.zf.reveal', function() {
                                dlg.remove();
                        });
                        reveal.open();
                    } else {
                        var frm = $('<form action="' + component.attr('href')
                                + '" method="post"></form>');
                        $('body').append(frm);
                        frm.submit();
                    }
                });
            });
        }
    };

    $.fn.postLink = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' + method + ' does not exist on jQuery.postLink');
        }
    };
}(jQuery));
