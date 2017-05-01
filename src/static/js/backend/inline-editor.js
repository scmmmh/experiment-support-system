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
                var component = $(this);
                // Handle clicking on the edit button
                component.on('click', 'a[data-action=edit]', function(ev) {
                    ev.preventDefault();
                    var link = $(this);
                    var container = link.parents('.editable-container');
                    container.removeClass('previewing').addClass('editing');
                    setTimeout(function() {
                        $(window).scrollTop(container.offset().top);
                    }, 50);
                });
                // Handle clicking on the cancel edits button
                component.on('click', 'a[data-action=cancel]', function(ev) {
                    ev.preventDefault();
                    var link = $(this);
                    var container = link.parents('.editable-container');
                    container.removeClass('editing').addClass('previewing');
                    container.find('form')[0].reset();
                });
                // Handle clicking on the save button
                component.on('click', 'a[data-action=save]', function(ev) {
                    ev.preventDefault();
                    var link = $(this);
                    var container = link.parents('.editable-container');
                    container.find('form').trigger('submit');
                });
                // Handle edit submission
                component.on('submit', 'form', function(ev) {
                    ev.preventDefault();
                    var form = $(this);
                    form.find('.is-invalid-label').removeClass('is-invalid-label');
                    form.find('.is-invalid-input').removeClass('is-invalid-input');
                    form.find('span.form-error.is-visible').removeClass('is-visible');
                    var promise = $.ajax(form.attr('action'), {
                        method: 'POST',
                        data: form.serialize()
                    });
                    promise.then(function(data) {
                        if(data.status == 'ok') {
                            var container = form.parents('.editable-container');
                            container.removeClass('editing').addClass('previewing');
                            container.find('.preview').empty().append($(data.fragment).children());
                        } else {
                            for(key in data.errors) {
                                var input = form.find('*[name=' + key + ']');
                                var label = input.parents('label');
                                var span = label.find('span.form-error');
                                if(span.length === 0) {
                                    span = $('<span class="form-error"></span>');
                                    label.append(span);
                                }
                                label.addClass('is-invalid-label');
                                input.addClass('is-invalid-input');
                                span.addClass('is-visible');
                                span.html(data.errors[key]);
                            }
                        }
                    });
                });
                // Handle add-a-row in a table editor clicks
                component.on('click', 'a[data-action=add-row]', function(ev) {
                    ev.preventDefault();
                    var link = $(this);
                    var row = link.parent().parent();
                    var new_row = row.clone();
                    new_row.find('a[data-action=add-row]').attr('data-action', 'remove-row').addClass('alert').removeClass('success');
                    new_row.find('.mdi').html('remove');
                    new_row.find('input').each(function() {
                        var input = $(this);
                        input.val('');
                        input.removeClass('hidden');
                    });
                    row.find('input').each(function() {
                        var input = $(this);
                        var count = parseInt(/[0-9]+/.exec(input.attr('name'))[[0]]) + 1;
                        input.attr('name', input.attr('name').replace(/[0-9]+/, count));
                    });
                    row.before(new_row);
                });
                // Handle remove-a-row in a table editor clicks
                component.on('click', 'a[data-action=remove-row]', function(ev) {
                    ev.preventDefault();
                    $(this).parent().parent().remove();
                });
                // Make the list of editable items sortable if the reorder option is set
                if(options.reorder) {
                    // Prevent clicking on the reorder button having an effec
                    component.on('click', 'a[data-action=reorder]', function(ev) {
                        ev.preventDefault();
                    });
                    component.sortable({
                        handle: 'a[data-action=reorder]',
                        containment: 'parent',
                        tolerance: 'pointer',
                        update: function() {
                            var item_ids = [];
                            $('article').children('div').each(function() {
                                item_ids.push($(this).data('item-id'));
                            });
                            $.ajax(options.reorder, {
                                method: 'POST',
                                data: $.param({csrf_token: options.csrf_token, item: item_ids}, true)
                            });
                        }
                    });
                }
            });
        }
    };

    $.fn.inlineEditor = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' + method + ' does not exist on jQuery.inlineEditor');
        }
    };
}(jQuery));
