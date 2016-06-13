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