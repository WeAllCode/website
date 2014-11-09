/**
CoderDojoChi.org Global JS

@class global
@namespace CDC
@type {Object}
**/

var CDC = CDC || {};

CDC.global = (function($, document, window, undefined) {
    "use strict";

    // app global properties


    /* Public Methods _________________________________________________________________ */

    function init() {

        // account for csrf in all ajax requests
        $.ajaxSetup({
            data: {csrfmiddlewaretoken: '{{ csrf_token }}' },
        });

        // remove any alerts
        setTimeout(function(){
            $('.alert-fade').parent().fadeOut();
        }, 3000);

        // Scroll
        $(window).scroll(function() {
            if ($(document).scrollTop() > 50) {
                $('nav').addClass('shrink');
            } else {
                $('nav').removeClass('shrink');
            }
        });
    }

    function openPopUp(url, height, width) {
        height = (height) ? height: 600;
        width = (width) ? width: 400;
        var newWindow = window.open(url, 'name', 'height=' + height + ',width=' + width);
        if (window.focus) { newWindow.focus() }
        return false;
    }

    /* Private Methods ________________________________________________________________ */


    /* Expose Public Methods ________________________________________________________________ */

    return {
        init: init,
        openPopUp: openPopUp
    };

}(jQuery, document, window, undefined));

$(function (){
    CDC.global.init();
});
