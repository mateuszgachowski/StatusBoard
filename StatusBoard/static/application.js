(function() {
    var channels = [],
        message_handlers = {},
        ajax_error = function() { alert('Communcation error.'); },
        on_started = function() {};
        
    var load_people = function(callback) {
        callback = callback || function() {};
        var request = $.ajax({
            'url': '/people',
            'type': 'GET',
            'error': ajax_error,
            'success': function(data) {
                window.SBApp.people = data;
                callback();
            }
        });
    };
    
    var load_statuses = function(queue_done) {
        var load_status = function(channel, callback) {
            channel = channel || null;
            callback = callback || function() {};
            
            if (channel === null) {
                return false;
            }
            
            $.ajax({
                'url': '/status/' + channel,
                'type': 'GET',
                'error': function() {
                    ajax_error();
                    queue_next();
                },
                'success': function(data) {
                    callback(data);
                }
            });
            
            return true;
        };
        
        var i = -1;
        var queue_next = function() {
            i += 1;
            var job = channels[i];
            
            if (job === undefined) {
                queue_done();
            } else {
                console.log(job);
                load_status(job, function(data) {
                    message_handlers[job].apply(message_handlers, [ data ]);
                    queue_next();
                });
            }
        };
        queue_next();
    };

    var h4x0r_people = function() {
        $.each(window.SBApp.people, function(key, value) {
            $.each($('img.person-' + key + '-avatar'), function(index, item) {
                $(item).attr('src', window.SBApp.gravatar_url(value.gravatar_hash, $(item).attr('data-avatar-size')));
            });
            $.each($('.person-' + key + '-name'), function(index, item) {
                $(item).text(value.name);
            });
        });
    };
    
    var start_event_source = function() {
        var event_source = new BTHEventSource('/events'),
            i = 0;
            
        for(i = 0; i < channels.length; i += 1) {
            event_source.message(channels[i], message_handlers[channels[i]]);
        }
        
        event_source.message('sysmsg', function(data) {
            if (data == 'h4x0r_people') {
                load_people(h4x0r_people);
            }
        });
        event_source.start();
        
        on_started();
    };
    
    window.SBApp = {
        'ajax_error': ajax_error,
        'set_channels': function(new_channels) {
            channels = new_channels;
        },
        'on': function(message, handler) {
            message_handlers[message] = handler;
        },
        'off': function(message) {
            message_handlers[message] = undefined;
        },
        'people': null,
        'gravatar_url': function(mail_hash, size) {
            size = size || 60;
            
            return 'http://gravatar.com/avatar/' + mail_hash + '?s=' + size;
        },
        'started': function(callback) {
            on_started = callback;
        },
        'start': function() {
            load_people(function() {
                load_statuses(function() {
                    start_event_source();
                });
            });
        }
    };
})();