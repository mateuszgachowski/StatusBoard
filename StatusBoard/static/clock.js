(function() {
    var clock = null,
        h_hours = null,
        h_minutes = null,
        h_seconds = null;
        
    var set_css_rotation = function(element, rotation) {
        if ((element != null) && (isNaN(rotation) == false)) {
            var value = 'rotate(' + rotation + 'deg)';
            element.css('-webkit-transform', value);
            element.css('-moz-transform', value);
            element.css('transform', value);
        }
    };
        
    var update_hands = function() {
        var current_date = new Date();
        set_css_rotation(h_seconds, current_date.getSeconds() * 6);
        set_css_rotation(h_minutes, current_date.getMinutes() * 6);
        
        var hours = current_date.getHours();
        if (hours >= 12) {
            hours -= 12;
        }
        set_css_rotation(h_hours, hours * 30);
    };
    
    $(function() {
        clock = $('#clock');
        h_hours = $('div.hand.hours', clock);
        h_minutes = $('div.hand.minutes', clock);
        h_seconds = $('div.hand.seconds', clock);
        update_hands();
        var interval = window.setInterval(update_hands, 1000);
    });
})();