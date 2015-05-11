if (!Cookies.get('kukiz_accept_cookies')) {
  $(function() {
    $('.alert.cookie.notice').css('display', 'block');
  });

  $('body').on('click', '.alert.cookie.notice a.close', function() {
    Cookies.set('kukiz_accept_cookies', 'http://media.giphy.com/media/whNK1SAMSQjwQ/giphy.gif')
  });
}

