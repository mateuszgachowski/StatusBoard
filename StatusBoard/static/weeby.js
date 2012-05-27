$(function() {   
    var xmpp_queue = (function() {
        var queue = [];
        var timeout = null;
        var current_index = 0;
        
        var next_message = function() {
            var message = queue[current_index];
            if (message === undefined) {
                return;
            }
            
            var show_new_msg = function() {
                var new_msg = $('<p id="msg"><img width="76" height="76" class="person-' + message.person + '-avatar" src="' + window.SBApp.gravatar_url(window.SBApp.people[message.person].gravatar_hash, 76) + '" data-avatar-size="76" alt="" />' + message.message + '</p>');
                new_msg.css('margin-top', -128);
                $('#news').append(new_msg);
                new_msg.animate({ 'margin-top': 0 }, function() {
                    timeout = window.setTimeout(next_message, 5000);
                });
                
                current_index += 1;
                if (current_index >= queue.length) {
                    current_index = 0;
                }
            };
            
            var old_msg = $('#msg');
            if (old_msg.length == 1) {
                old_msg.animate({ 'margin-top': 128 }, function() {
                    old_msg.remove();
                    show_new_msg();
                });
            } else {
                show_new_msg();
            }
        };
        
        return {
            'add': function(item) {
                queue.unshift(item);
                current_index = 0;
                for(var i = 0; i < queue.length - 5; i++) {
                    queue.pop();
                }
                
                if (timeout === null) {
                    next_message();
                }
            },
            'init': function(items) {
                queue = [];
                $.each(items, function(index, item) {
                    queue.push(item);
                });
            },
            'start': function() {
                if (timeout === null) {
                    next_message();
                }
            },
            'stop': function() {
                if (timeout !== null) {
                    window.clearTimeout(timeout);
                    timeout = null;
                }
            }
        }
    })();
    
    window.SBApp.on('pinger', function(data) {
        $('#present strong').text(data.active);
        $('#absent strong').text(data.inactive);
    });
    
    var projects_scroll_timeout = null;
    var scroll_projects = function() {
        var content = $('#content'),
            table = $('#projects'),
            new_top = 0;
        
        window.clearTimeout(projects_scroll_timeout);
        if (table.outerHeight() > content.outerHeight()) {
            if (parseInt(table.css('top'), 10) == 0) {
                new_top = -1 * (table.outerHeight() - content.outerHeight());
            } else {
                new_top = 0;
            }
            table.animate({ 'top': new_top }, function() {
                projects_scroll_timeout = window.setTimeout(scroll_projects, 5000);
            });
        }
    };
    
    window.SBApp.on('redmine', function(data) {
        var count = 0;            
        var row_class = 'odd';
        
        var make_row = function(entry) {
            var row = $('<tr class="' + row_class + '" id="project-' + entry.id + '" data-project-id="' + entry.id + '"></tr>');
            
            var cell_name = $('<td class="name">' + entry.name + '</td>');            
            row.append(cell_name);
                        
            var tasks_total = entry.issues['2'].open + entry.issues['2'].closed;
            var cell_tasks = $('<td class="tasks">' + entry.issues['2'].open + ' open / <span>' + tasks_total + '</span></td>');
            row.append(cell_tasks);
            
            var errors_total = entry.issues['2'].open + entry.issues['2'].closed;
            var cell_errors = $('<td class="errors">' + entry.issues['2'].open + ' open / <span>' + errors_total + '</span></td>');
            row.append(cell_errors);
            
            var cell_people = $('<td class="persons"><ul></ul></td>');
            row.append(cell_people);    
            var people_list = $('ul', cell_people);       
            
            $.each(entry.people, function(index, item) {
                var person_item = $('<li><img width="60" height="60" class="person-' + item + '-avatar" src="' + window.SBApp.gravatar_url(window.SBApp.people[item].gravatar_hash) + '" data-avatar-size="60" alt="" /><span class="person-' + item + '-name">' + window.SBApp.people[item].name + '</span></li>');
                people_list.append(person_item);
            });
            
            return row;
        };
        
        window.clearTimeout(projects_scroll_timeout);
        var projects_table = $('#projects tbody');
        projects_table.empty();
        $('#projects').css('top', 0);
        $.each(data.projects, function(index, item) {
            var new_row = make_row(item);
            projects_table.append(new_row);
            
            count += 1;
            row_class = (row_class === 'odd') ? 'even' : 'odd';
        });
        
        $('#projects_count strong').text(count);
        projects_scroll_timeout = window.setTimeout(scroll_projects, 5000);
    });
    
    window.SBApp.on('weather', function(data) {
        var container = $('#weather'),
            img = $('img', container);
        img.attr('src', '/static/weather-icons/' + data.icon_code + '.png');
        img.attr('alt', data.description);
        img.attr('title', data.description);
        
        $('strong', container).text(data.temperature + '°' + data.temperature_unit);
        $('span', container).text(data.city);
    });
    
    window.SBApp.on('xmpp', function(data) {
        if (data.hasOwnProperty('person') === false) {
            xmpp_queue.init(data);
            xmpp_queue.start();
        } else {
            xmpp_queue.add(data);
        }
    });
    
    window.SBApp.set_channels([ 'pinger', 'redmine', 'weather', 'xmpp' ]);
    window.SBApp.started(function() {
        var blanker_timeout = null,
            blanker = $('#blanker');       
                
        var hide_blanker = function() {
            window.clearTimeout(blanker_timeout);
            blanker.removeClass('visible');
            blanker_timeout = window.setTimeout(show_blanker, 2*60*1000);
        };
                
        var show_blanker = function() {
            window.clearTimeout(blanker_timeout);
            blanker.addClass('visible');
            blanker_timeout = window.setTimeout(hide_blanker, 5*1000);
        };
        
        hide_blanker();
    });
    
    window.SBApp.start();
});