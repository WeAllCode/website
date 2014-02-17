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

    var $thing;

    /* Public Methods _________________________________________________________________ */

    function init() {

        // account for csrf in all ajax requests
        $.ajaxSetup({
            data: {csrfmiddlewaretoken: '{{ csrf_token }}' },
        });

        // select dom elements
        $thing = $('.thing');

        // attach events
        $(document)
            .on('click', '.thing', click);

        // remove any alerts
        setTimeout(function(){
            $('.alert').fadeOut();
        }, 3000);
    }

    /* Private Methods ________________________________________________________________ */

    function click() {
        console.log('clicked thing');
    }

    /* Expose Public Methods ________________________________________________________________ */

    return {
        init: init
    };

}(jQuery, document, window, undefined));

$(function (){
    CDC.global.init();
});
