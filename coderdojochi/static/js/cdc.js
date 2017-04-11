/**
CoderDojoChi.org Global JS

@class global
@namespace CDC
@type {Object}
**/

var CDC = CDC || {};

CDC.global = (function($, document, window, undefined) {
    'use strict';

    /* Public Methods _________________________________________________________________ */

    function init() {

        $('[data-toggle="popover"]').popover({
            html: true,
            container: 'body'
        });

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

        // display any global messages

        setTimeout(function() {
            $('.global-messages:first')
                .animate({
                    top: 0
                }, 250)
                .css('zIndex', 1033);
        }, 500);

        // Scroll listener

        $(window).scroll(function() {
            if ($(document).scrollTop() > 50) {
                $('nav').addClass('shrink');
            } else {
                $('nav').removeClass('shrink');
            }
        });

        // attach event listeners to document

        $(document)
            // Student form field expand/hide
            .on('click', '.js-expand-student-form', expandStudentForm)
            // Login / Register email show/hide
            .on('click', '.login-email, .signup-email', displayRegistrationEmailForm)
            .on('click', '.global-messages .global-messages-close', closeGlobalMessages);

        $('#id_phone').mask('(999) 999-9999');
        $('#id_zip').mask('99999');
    }

    function openPopUp(url, height, width) {
        height = (height) ? height : 500;
        width = (width) ? width : 600;
        var newWindow = window.open(url, 'name', 'height=' + height + ',width=' + width);
        if (window.focus) {
            newWindow.focus();
        }
        return false;
    }

    /* Private Methods ________________________________________________________________ */

    function expandStudentForm(e) {

        var $this = $(e.target),
            text = $this.text();

        $this.parent().parent().find('textarea').toggleClass('hidden');

        if (text === 'expand') {
            $this.text('contract');
        } else {
            $this.text('expand');
        }
    }

    function displayRegistrationEmailForm() {
        var $form = $('.main .container form');
        $form.toggleClass('hide');
        $form.find('input:not([type=hidden]):eq(0)').focus();
    }

    function closeGlobalMessages() {
        $('.global-messages:first').animate({
            top: '-100px'
        }, 250, function() {
            $(this).remove();
        });
    }

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
