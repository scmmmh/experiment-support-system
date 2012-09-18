$(document).ready(function() {
	$('.question.ranking ul select').hide();
    $('.question.ranking ul').sortable({
    	items: 'li:not(.role-label)',
    	update: function(e, ui) {
    		var items = $(this).sortable('toArray');
    		for(var idx in items) {
    			var id = '#' + items[idx].replace(/\./g, '\\.');
    			id = id.substring(0, id.length - 5);
    			$(id).val(idx);
    		}
    	}
    });
    $('.question.ranking ul li.role-label').show();
    $('input.role-other-text').keypress(function() {
        var other_name = $(this).attr('name');
        other_name = other_name.substring(0, other_name.lastIndexOf('.')) + '.answer';
        $('input[name="' + other_name + '"][value="_other"]').attr('checked', 'checked');
        $('select[name="' + other_name + '"]').val('_other');
    });
    $('select.role-with-other').each(function() {
    	var select = $(this);
    	var other_text = select.parent().find('input.role-other-text');
		if(select.val() == '_other') {
			other_text.show();
		} else {
			other_text.hide();
		}
    	select.change(function() {
    		if(select.val() == '_other') {
    			other_text.show();
    		} else {
    			other_text.hide();
    		}
    	})
    });
});
