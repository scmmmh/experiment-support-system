/*
Copyright (c) 2003-2011, CKSource - Frederico Knabben. All rights reserved.
For licensing, see LICENSE.html or http://ckeditor.com/license
*/

CKEDITOR.editorConfig = function( config )
{
	config.toolbar = 'PyQuest';
	
	config.toolbar_PyQuest = [
	                          {name: 'document', items: ['Source']}
	                          {name: 'clipboard', items : ['Cut','Copy','Paste','PasteText','PasteFromWord','-','Undo','Redo']},
	                          {name: 'basicstyles', items : ['Bold','Italic','Underline','Strike','Subscript','Superscript','-','RemoveFormat']},
	                          {name: 'paragraph', items : ['NumberedList','BulletedList','-','Outdent','Indent','-','Blockquote','CreateDiv',
	                                                         '-','JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock','-','BidiLtr','BidiRtl']},
	                          {name: 'links', items : ['Link','Unlink','Anchor' ]},
	                          {name: 'insert', items : ['Image','Table','HorizontalRule','SpecialChar']},
	                          {name: 'styles', items : [ 'Styles','Format','Font','FontSize' ] },
	                          {name: 'colors', items : [ 'TextColor','BGColor' ] }
	];
};
