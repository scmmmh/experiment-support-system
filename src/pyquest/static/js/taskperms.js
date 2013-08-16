function fix_multiple_selects()
{
    var text = $('#task-disallow-repeater').text();
    var bits = text.replace(/[\[\]]/g, '').split(',')
    for (var i = 0; i < bits.length; i++)
    {
	$('[name="task_disallow"] option').filter(function() { 
	    var rtrn = $(this).val() == bits[i];
	    return rtrn;}).prop('selected', true);
    }
    bits = $('#task-order-repeater').text().split(',');
    for (var i = 0; i < bits.length; i++)
    {
	$('[name="task_order"] option').filter(function() { return $(this).val() == bits[i];}).prop('selected', true);
    }
    bits = $('#interface-disallow-repeater').text().split(',');
    for (var i = 0; i < bits.length; i++)
    {
	$('[name="interface_disallow"] option').filter(function() { return $(this).val() == bits[i];}).prop('selected', true);
    }
    bits = $('#interface-order-repeater').text().split(',');
    for (var i = 0; i < bits.length; i++)
    {
	$('[name="interface_order"] option').filter(function() { return $(this).val() == bits[i];}).prop('selected', true);
    }

    bits = $('#applies-to-repeater').text().split(',');
    for (var i = 0; i < bits.length; i++)
    {
	$('[name="qsheet"] option').filter(function() { return $(this).val() == bits[i];}).prop('selected', true);
    }
}

function set_restriction_appearances()
{
    if ($('[name="task_worb"]').val() == 'w')
    {
	$('.task-restriction').css({'visibility':'visible'});
    }
    else
    {
	$('.task-restriction').css({'visibility':'hidden'});
    }
    if ($('[name="interface_worb"]').val() == 'w')
    {
	$('.interface-restriction').css({'visibility':'visible'});
    }
    else
    {
	$('.interface-restriction').css({'visibility':'hidden'});
    }
}

function display_participant_count(url)
{
    var worb = $('[name="task_worb"]').val() + $('[name="interface_worb"]').val();
    var tcount = parseInt($('[name="task_count"]').val());
    var icount = parseInt($('[name="interface_count"]').val());
    var tcon = $('[name="task_disallow"]').val().join(','); 
    var icon = $('[name="interface_disallow"]').val().join(',');
    var tord = $('[name="task_order"]').val().join(',');
    var iord = $('[name="interface_order"]').val().join(',');
    
//    $.ajax('${r.route_url("survey.qsheet.pcount", sid=survey.id, qsid=qsheet.id)}', 
    $.ajax(url, 
	   {
	       data: {"worb" : worb, "tcount" : tcount, "icount": icount, "tcon":tcon, "icon":icon, "tord":tord, "iord":iord},
	       success: function(response) {
                   $('span.task-spec').html(response);
		   set_task_buttons(url);
		   set_restriction_appearances();
		   fix_multiple_selects();
	       },
               error: function(xhr, ts, et) {
                   var x = 100;
               }
	   })
}

function set_task_buttons(url)
{
       $('.role-qsheet-permute').change(function(ev){
           display_participant_count(url);});
}

function task_init(url)
{
    set_task_buttons(url);
    set_restriction_appearances();
    fix_multiple_selects();
//    display_participant_count(url);
}