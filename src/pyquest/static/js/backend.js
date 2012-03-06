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

function setup_status_changer() {
	var status_box = $('div.survey-status');
	if(!status_box.hasClass('no-menu')) {
		status_box.hover(function() {
			status_box.children('.status-changer').slideDown();
		}, function() {
			status_box.children('.status-changer').slideUp();
		});
	}
}