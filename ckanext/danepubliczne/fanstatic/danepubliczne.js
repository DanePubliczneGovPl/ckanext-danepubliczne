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
  $('.fileupload').fileupload({
    done: function (e, data) {
            $.each(data.result.files, function (index, file) {
                //$('<p/>').text(file.name).appendTo(document.body);
                window.alert(file.name);
            });
        }
  });
});