!function(t){var e={init:function(e){return this.each(function(){var e=t(this);e.on("click",function(){e.parent().siblings(".question-help").slideToggle()})})}};t.fn.toggle_question_help=function(i){return e[i]?e[i].apply(this,Array.prototype.slice.call(arguments,1)):"object"!=typeof i&&i?void t.error("Method "+i+" does not exist on jQuery.toggle_question_help"):e.init.apply(this,arguments)}}(jQuery);