$(document).foundation()

$(document).ready(function () {

  // Accessible smooth scroll
  // From https://css-tricks.com/smooth-scrolling-accessibility/
  function filterPath(string) {
    return string
      .replace(/^\//, '')
      .replace(/(index|default).[a-zA-Z]{3,4}$/, '')
      .replace(/\/$/, '');
  }

  var locationPath = filterPath(location.pathname);
  $('a[href*="#"]:not([href="#"])').each(function () {
    var thisPath = filterPath(this.pathname) || locationPath;
    var hash = this.hash;
    if ($("#" + hash.replace(/#/, '')).length) {
      if (locationPath == thisPath && (location.hostname == this.hostname || !this.hostname) && this.hash.replace(/#/, '')) {
        var $target = $(hash),
          target = this.hash;
        if (target) {
          $(this).click(function (event) {
            event.preventDefault();
            $('html, body').animate({
              scrollTop: $target.offset().top
            }, 1000, function () {
              location.hash = target;
              $target.focus();
              if ($target.is(":focus")) { //checking if the target was focused
                return false;
              } else {
                $target.attr('tabindex', '-1'); //Adding tabindex for elements not focusable
                $target.focus(); //Setting focus
              };
            });
          });
        }
      }
    }
  });

  // Nav toggler
  $('.mobile-nav-trigger').click(function () {
    $('.mobile-nav').toggleClass('hide');
    $('.main-logo').toggleClass('show');
  });

  $('[data-toggler]').click(function() {
    $($(this).data('toggler')).toggleClass($(this).data('toggle-class'));
  });
});
