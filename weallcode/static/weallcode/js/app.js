$(document).foundation()

$(document).ready(function() {
  $('a[href*="#"]').click(function(e) {
    const parts = $(this).attr('href').split('#');
    const path = parts[0];

    if (parts.length === 1 || path !== window.location.pathname) return;

    e.preventDefault();

    const id = parts[1];

    $([document.documentElement, document.body]).animate({
      scrollTop: $('#' + id).offset().top
    }, 1500);
  });

  $('.mobile-nav-trigger').click(function() {
    $('.mobile-nav').toggleClass('hide');
    $('.main-logo').toggleClass('show');
  });
});
