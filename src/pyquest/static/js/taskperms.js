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
    var tcon = $('[name="task_disallow"]').val()
    if (tcon)
    {
	tcon = tcon.join(',')
    }
    else
    {
	tcon = ' '
    }
    
    var icon = $('[name="interface_disallow"]').val();
    var tord = $('[name="task_order"]').val();
    var iord = $('[name="interface_order"]').val();
    
//    $.ajax('${r.route_url("survey.qsheet.pcount", sid=survey.id, qsid=qsheet.id)}', 
    $.ajax(url, 
	   {
	       data: {"worb" : worb, "tcount" : tcount, "icount": icount, "tcon":tcon, "icon":icon, "tord":tord, "iord":iord},
	       success: function(response) {
                   $('dd.task-spec').html(response);
		   set_task_buttons(url);
		   set_restriction_appearances();

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
    display_participant_count(url);
    set_task_buttons(url);
    set_restriction_appearances();
}