function getLocation(href) {
    var match = href.match(/^(https?\:)\/\/(([^:\/?#]*)(?:\:([0-9]+))?)(\/[^?#]*)(\?[^#]*|)(#.*|)$/);
    return match && {
        protocol: match[1],
        host: match[2],
        hostname: match[3],
        port: match[4],
        pathname: match[5],
        search: match[6],
        hash: match[7]
    }
}

var DatasetPicker = function(div) {
	this.init(div);
}

$.extend(DatasetPicker.prototype, {
	init: function(div) {
		
		this.div = $(div);
		if( !this.div.length )
			return false;
			
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
		
		var that = this;
		
		var inp = $('<input>');
		inp.attr('type', 'text').attr('name', 'dataset_name').attr('placeholder', this.placeholder).blur(function(event){
			that.checkInput(inp);
		});
		
		if( value )
			inp.val( value );
		else
			inp.val('');
		
		var that = this;
		
		var controlls = $('<div>').addClass('controlls');
		var remove_btn = $('<a>').attr('href', '#').attr('title', 'Usuń zbiór').addClass('remove').click(function(event){
			event.preventDefault();
			that.removeInput(inp);
		});
		controlls.append(remove_btn);
		
		var inp_div = $('<div>').addClass('inp_group');	
		var inp_cont = $('<div>').addClass('inp_cont').append(inp);
		var status = $('<div>').addClass('status').html('<span class="ok" title="Zbiór istnieje na platformie danepubliczne.gov.pl"></span><span class="notok" title="Zbiór nie istnieje na platformie danepubliczne.gov.pl"></span>');
		
		inp_div.append(controlls).append(inp_cont).append(status);
		this.inputs_div.append(inp_div);
				
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
		
	},
	checkInput: function(inp) {
		
		var status = inp.parents('.inp_group').find('.status');
		status.find('span').hide();
		
		var v = $.trim(inp.val());
		var l = getLocation(v);
		var output = l ? l.pathname : v;
		
		console.log(output);
		
		var pos = output.indexOf('/dataset/')
	    if( pos != -1 )
	        output = output.substr(9);
	        	        
	    var pos = output.indexOf('/')
	    if( pos != -1 )
	        output = output.substr(0, pos);
	        			
		inp.val(output);
		
		if( output ) {
		
			$.ajax({
		        type: 'HEAD',
		        url: '/dataset/' + output,
		        complete: function(xhr) {
		            if( xhr.status == 200 ) {
			            status.find('.ok').css({display: 'inline'});
		            } else {
			            status.find('.notok').css({display: 'inline'});
		            }
		        }
			});
		
		} else {
			
			status.find('.notok').css({display: 'inline'});
			
		}
		
	}
});

// cookies
if (!Cookies.get('kukiz_accept_cookies')) {
  $(function() {
    $('.alert.cookie.notice').css('display', 'block');
  });

  $('body').on('click', '.alert.cookie.notice a.close', function() {
    Cookies.set('kukiz_accept_cookies', 'http://media.giphy.com/media/whNK1SAMSQjwQ/giphy.gif')
  });
}

// initilize fileupload
$(function() {
  if ($('.fileupload').length) {
    $('.fileupload').fileupload({
      done: function (e, data) {
              $.each(data.result.files, function (index, file) {
                  entry = '<span class="filename">'+ file.name +'</span>'
                    + '<span style="display:none" class="url">' + file.url + '</span><br/>'
                    + '<a class="article-add-image">Wstaw obraz</a>'
                    + ', <a class="article-add-link">Wstaw link</a>';

                  list = $(e.target).closest('.upload-panel').find('.files ul');
                  $('<li/>').html(entry).appendTo(list);
              });
          }
    });
  }
});

function article_insert(link_elem, text) {
  textarea = $(link_elem).closest('.markdown_with_upload').find('textarea');
  pos = textarea.prop("selectionStart");

  val = textarea.val();
  val_new = val.substring(0, pos) + text + val.substring(pos);
  textarea.val(val_new);
}

$('body').on('click', '.article-add-image', function(e) {
  url = $(e.target).siblings('.url').text();
  filename = $(e.target).siblings('.filename').text();

  article_insert(e.target, '<img src="' + url + '" alt="" title="'+ filename +'"/>');
});

$('body').on('click', '.article-add-link', function(e) {
  url = $(e.target).siblings('.url').text();
  filename = $(e.target).siblings('.filename').text();

  article_insert(e.target, '[' + filename +']('+ url + ')');
});

$('a[href="#field-sitewide-search"]').click(function(e){
    e.preventDefault();
    window.location = '#field-sitewide-search';
    document.getElementById("field-sitewide-search").focus();
    return false;
})

$(document).ready(function(){
	_dp = new DatasetPicker('.datasets_picker');
});
var _dp;