!function(e){var t={init:function(t){return this.each(function(){var a=e(this);a.on("click","a[data-action=edit]",function(t){t.preventDefault();var a=e(this),n=a.parents(".editable-container");n.removeClass("previewing").addClass("editing"),setTimeout(function(){e(window).scrollTop(n.offset().top)},50)}),a.on("click","a[data-action=cancel]",function(t){t.preventDefault();var a=e(this),n=a.parents(".editable-container");n.removeClass("editing").addClass("previewing"),n.find("form")[0].reset()}),a.on("click","a[data-action=save]",function(t){t.preventDefault();var a=e(this),n=a.parents(".editable-container");n.find("form").trigger("submit")}),a.on("submit","form",function(t){t.preventDefault();var a=e(this);a.find(".is-invalid-label").removeClass("is-invalid-label"),a.find(".is-invalid-input").removeClass("is-invalid-input"),a.find("span.form-error.is-visible").removeClass("is-visible");var n=e.ajax(a.attr("action"),{method:"POST",data:a.serialize()});n.then(function(t){if("ok"==t.status){var n=a.parents(".editable-container");n.removeClass("editing").addClass("previewing"),n.find(".preview").empty().append(e(t.fragment).children())}else for(key in t.errors){var i=a.find("*[name="+key+"]"),r=i.parents("label"),o=r.find("span.form-error");0===o.length&&(o=e('<span class="form-error"></span>'),r.append(o)),r.addClass("is-invalid-label"),i.addClass("is-invalid-input"),o.addClass("is-visible"),o.html(t.errors[key])}})}),a.on("click","a[data-action=add-row]",function(t){t.preventDefault();var a=e(this),n=a.parent().parent(),i=n.clone();i.find("a[data-action=add-row]").attr("data-action","remove-row").addClass("alert").removeClass("success"),i.find(".mdi").html("remove"),i.find("input").each(function(){var t=e(this);t.val(""),t.removeClass("hidden")}),n.find("input").each(function(){var t=e(this),a=parseInt(/[0-9]+/.exec(t.attr("name"))[[0]])+1;t.attr("name",t.attr("name").replace(/[0-9]+/,a))}),n.before(i)}),a.on("click","a[data-action=remove-row]",function(t){t.preventDefault(),e(this).parent().parent().remove()}),t.reorder&&(a.on("click","a[data-action=reorder]",function(e){e.preventDefault()}),a.sortable({handle:"a[data-action=reorder]",containment:"parent",tolerance:"pointer",update:function(){var a=[];e("article").children("div").each(function(){a.push(e(this).data("item-id"))}),e.ajax(t.reorder,{method:"POST",data:e.param({csrf_token:t.csrf_token,item:a},!0)})}}))})}};e.fn.inlineEditor=function(a){return t[a]?t[a].apply(this,Array.prototype.slice.call(arguments,1)):"object"!=typeof a&&a?void e.error("Method "+a+" does not exist on jQuery.inlineEditor"):t.init.apply(this,arguments)}}(jQuery),function(e){var t={init:function(t){return this.each(function(){var t=e(this);t.on("click",function(a){a.preventDefault();var n=t.data("ess-confirm");if(n){var i='<div id="confirm-modal" class="reveal" data-reveal=""><h2>'+(n.title||"Please confirm")+"</h2><p>"+n.msg+'</p><div class="text-right">';n.cancel&&(i=i+'<a href="#" class="button cancel '+(n.cancel.class_||"")+'">'+(n.cancel.label||"Cancel")+"</a>&nbsp;"),n.ok&&(i=i+'<a href="#" class="button ok '+(n.ok.class_||"")+'">'+(n.ok.label||"Ok")+"</a>"),i+="</div></div>";var r=e(i);e("body").append(r);var o=new Foundation.Reveal(r);r.find("a.cancel").on("click",function(e){e.preventDefault(),o.close()}),r.find("a.ok").on("click",function(a){a.preventDefault();var n=e('<form action="'+t.attr("href")+'" method="post"></form>');e("body").append(n),n.submit()}),e(document).on("closed.zf.reveal",function(){r.remove()}),o.open()}else{var s=e('<form action="'+t.attr("href")+'" method="post"></form>');e("body").append(s),s.submit()}})})}};e.fn.postLink=function(a){return t[a]?t[a].apply(this,Array.prototype.slice.call(arguments,1)):"object"!=typeof a&&a?void e.error("Method "+a+" does not exist on jQuery.postLink"):t.init.apply(this,arguments)}}(jQuery),function(e){var t={init:function(t){return this.each(function(){var t=e(this);e(window).on("resize",function(){t.sidebar("update")}).on("scroll",function(){t.sidebar("update")})}).sidebar("update")},update:function(){var t=e(this),a=e(window).innerHeight(),n=0;t.parent().siblings("header").each(function(){n+=e(this).outerHeight(!0)});var i=e(window).scrollTop();i<n?(a=a-n+i,e("#sidebar").css("position","").css("height",a+"px")):e("#sidebar").css("position","fixed").css("top","0px").css("height",a+"px")}};e.fn.sidebar=function(a){return t[a]?t[a].apply(this,Array.prototype.slice.call(arguments,1)):"object"!=typeof a&&a?void e.error("Method "+a+" does not exist on jQuery.sidebar"):t.init.apply(this,arguments)}}(jQuery);