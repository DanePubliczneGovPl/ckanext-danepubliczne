var DatasetPicker = function(div) {
	this.init(div);
}

$.extend(DatasetPicker.prototype, {
	init: function(div) {
		
		this.div = $(div);
		this.placeholder = this.div.data('placeholder');
		
		this.build();
		
		var init_value = this.div.data('value');
		if( init_value ) {
			
			var values = init_value.split('&');
			for( var i=0; i<values.length; i++ ) {
				this.addInput(values[i]);
			}
			
		}
		
		console.log(init_value);
		
	},
	build: function() {
		
		this.inputs_div = $('<div>').addClass('inputs');
		this.controlls_div = $('<div>').addClass('controlls');
		
		var that = this;
		
		var a = $('<a>').addClass('add').attr('href', '#').text('Dodaj zbiór danych').click(function(event){
			event.preventDefault();
			that.addInput(false);
		});
		
		this.div.append(this.inputs_div).append(this.controlls_div.append(a));
		
	},
	addInput: function(value) {
		
		var inp = $('<input>');
		inp.attr('type', 'text').attr('name', 'dataset_name').attr('placeholder', this.placeholder);
		
		if( value )
			inp.val( value );
		else
			inp.val('');
		
		var that = this;
		
		var controlls = $('<div>').addClass('controlls');
		var remove_btn = $('<a>').attr('href', '#').addClass('remove').click(function(event){
			event.preventDefault();
			that.removeInput(inp);
		});
		controlls.append(remove_btn);
		
		var inp_div = $('<div>').addClass('inp_group');	
		var inp_cont = $('<div>').addClass('inp_cont').append(inp);
		
		inp_div.append(inp_cont).append(controlls);
		this.inputs_div.append(inp_div);
		
		if( !value )
			inp.focus();
				
	},
	removeInput: function(inp) {
		
		var inp_group = inp.parents('.inp_group');
		
		if( inp_group.length ) {
			
			var inp = inp_group.find('input');
			var v = $.trim( inp.val() );
						
			if( v ) {
				if( confirm('Czy na pewno chcesz usunąć ten zbiór danych?') )
					inp_group.remove();
			} else {
				inp_group.remove();
			}
			
		}
		
	}
});

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
	
	dp = new DatasetPicker('.datasets_picker');
	
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

var dp;