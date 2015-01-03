/**
CoderDojoChi.org Global JS

@class global
@namespace CDC
@type {Object}
**/

var CDC = CDC || {};

CDC.global = (function($, document, window, undefined) {
    'use strict';

    // app global properties


    /* Public Methods _________________________________________________________________ */

    function init() {

        // account for csrf in all ajax requests
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                function getCookie(name) {
                    var cookieValue = null;
                    if (document.cookie && document.cookie !== '') {
                        var cookies = document.cookie.split(';');
                        for (var i = 0; i < cookies.length; i++) {
                            var cookie = jQuery.trim(cookies[i]);
                            // Does this cookie string begin with the name we want?
                            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }
                        }
                    }
                    return cookieValue;
                }
                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    // Only send the token to relative URLs i.e. locally.
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            }
        });

        // remove any alerts
        setTimeout(function() {
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
        height = (height) ? height : 600;
        width = (width) ? width : 400;
        var newWindow = window.open(url, 'name', 'height=' + height + ',width=' + width);
        if (window.focus) {
            newWindow.focus();
        }
        return false;
    }

    /* Private Methods ________________________________________________________________ */


    /* Expose Public Methods ________________________________________________________________ */

    return {
        init: init,
        openPopUp: openPopUp
    };

}(jQuery, document, window, undefined));

$(function() {
    'use strict';
    CDC.global.init();
});
