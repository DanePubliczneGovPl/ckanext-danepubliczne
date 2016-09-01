$(document).ready(function(){
	$('#field-date').datepicker({
		format: 'yyyy-mm-dd',
	}).on('changeDate', function(event){
		$(event.target).datepicker('hide');
	});
});