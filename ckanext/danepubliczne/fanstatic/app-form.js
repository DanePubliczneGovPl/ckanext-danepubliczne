function today() {
	var today = new Date();
	var dd = today.getDate();
	var mm = today.getMonth()+1;
	var yyyy = today.getFullYear();
	
	if(dd<10) {
	    dd='0'+dd
	} 
	
	if(mm<10) {
	    mm='0'+mm
	} 
	
	today = yyyy + '-' + mm + '-' + dd;
	return today;
}

$(document).ready(function(){
		
	var date_inp = $('#field-date');
	if( date_inp.length ) {
		
		var v = $.trim(date_inp.val());
		
		if( !v )
			date_inp.val(today());
		
		date_inp.datepicker({
			format: 'yyyy-mm-dd',
		}).on('changeDate', function(event){
			$(event.target).datepicker('hide');
		});
	
	}
	
});