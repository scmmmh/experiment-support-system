CSRF_TOKEN = ''
function post_submit() {
	var $this = $(this);
	var ok = true;
	if($this.data('confirm')) {
		if($this.data('confirm') != 'no-confirm') {
			ok = confirm($this.data('confirm'));
		}
	} else {
		ok = confirm('Please confirm this action');
	}
	if(ok) {
		var form = $(document.createElement('form'));
		$this.append(form);
		var href = $(this).attr('href')
		form.attr('action', href);
		form.attr('method', 'post');
		form.append($('<input type="hidden" name="csrf_token" value="' + CSRF_TOKEN + '"/>'));
		if(href.indexOf('?') > 0) {
			var items = href.substring(href.indexOf('?') + 1).split('&');
			for(var idx = 0; idx < items.length; idx++) {
				var pair = items[idx].split('=');
				if (pair.length==2) {
					form.append($('<input type="hidden" name="' + pair[0] + '" value="' + pair[1] + '"/>'))
				}
			}
		}
		form.submit();
	}
	return false;
}

function make_toggle_link(id) {
	var elem = $('#' + id);
	var toggle = $('#' + id + '-toggle');
	elem.hide();
	var link = $('<a href="#"></a>').click(function() {
		elem.slideToggle();
		return false;
	}).html(toggle.html());
	toggle.html(link);
}