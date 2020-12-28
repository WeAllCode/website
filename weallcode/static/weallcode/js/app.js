$(document).foundation();

$(document).ready(function () {
  // Nav toggler
  $(".mobile-nav-trigger").click(function () {
    $(".mobile-nav").toggleClass("hide");
    $(".main-logo").toggleClass("show");
  });

  $("[data-toggler]").click(function () {
    $($(this).data("toggler")).toggleClass($(this).data("toggle-class"));
  });

  $(".autoreveal").each(function () {
    $(this).foundation("open");
  });
});
