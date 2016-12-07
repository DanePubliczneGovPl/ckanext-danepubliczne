Dropzone.autoDiscover = false;
$(document).ready(function(){

	var myDropzone = new Dropzone("#dropzone-div", {
		url: "/application/upload",
		maxFiles: 1,
		previewsContainer: '#dropzone-previews',
		paramName: 'image',
		hiddenInputContainer: '#dropzone-inputs',
		uploadMultiple: false,
		addRemoveLinks: true,
		success: function(file){
			if( file.status === 'success' ) {
				$('#image_field').val( file.xhr.responseText );
			}
		},
		sending: function() {
			$('.dropzone-div-cont').hide();
		},
		addedFile: function() {
			$('.dropzone-div-cont').hide();
		},
		removedFile: function() {
			$('#image_field').val('');
		},
		canceled: function() {
			$('.dropzone-div-cont').show();
			$('#image_field').val('');
		},
		reset: function() {
			$('.dropzone-div-cont').show();
			$('#image_field').val('');
		},
		dictRemoveFile: 'Usuń obraz',
		dictCancelUpload: 'Zatrzymaj wysyłanie',
		dictCancelUploadConfirmation: 'Czy na pewno chcesz zatrzymać wysyłanie?'
	});

});