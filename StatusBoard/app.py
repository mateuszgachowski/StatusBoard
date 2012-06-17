# -*- coding: utf-8 -*-
"""Application class."""

import brukva
import cPickle
import logging
import tornado.web
import tornado.httpclient
import StatusBoard.handlers
import os.path
import btheventsource

class StatusBoardApplication(tornado.web.Application):
    """Custom tornado.web.Application subclass."""
    
    channels = set()
    workers = dict()
    statuses = dict()
    
    redis = None
        
    @classmethod
    def add_listener(self, channel_name, channel_listener):
        """Registers a listener for the channel."""    
        self.channels.add(channel_listener)
        
    @classmethod
    def remove_listener(self, channel_name, channel_listener):
        """Registers a listener from the channel."""
        self.channels.remove(channel_listener)
        
    def _update_status(self, channel_name, message):
        """Updates Redis status for a worker."""
        self.redis.set('StatusBoard:status:' + channel_name, cPickle.dumps(message))
        
    def register_worker(self, channel_name, worker):
        """Registers a worker for a channel."""
        self.workers[channel_name] = worker
        
        if self.settings.get('mode', 'master') == 'master':
            self._update_status(channel_name, worker.status())
        else:
            self.redis.get('StatusBoard:status:' + channel_name,
                           lambda status: self.statuses.update({ channel_name: status }))
    
    def remove_worker(self, channel_name):
        """Removes a worker for a channel."""
        del(self.workers[channel_name])
        
    def start_workers(self):
        """Starts registered workers."""
        if self.settings.get('mode', 'master') == 'master':
            for channel_name in self.workers:
                self.workers[channel_name].start()
        else:
            redis_channels = [ 'StatusBoard:' + channel for channel in self.workers.keys() ]
            redis_channels.append('StatusBoard:sysmsg')
            self.redis.subscribe(redis_channels)
            self.redis.listen(self._on_message)
            
    def _on_message(self, message):
        """Callback for Redis PubSub listener."""
        channel_name = message.channel.replace('StatusBoard:', '')
        body = cPickle.loads(message.body)
        
        if channel_name == 'sysmsg':
            if body['command'] == 'h4x0r_people':
                StatusBoard.handlers.PeopleHandler._h4x0r3d = body['payload']
            
            body = body['command']
        
        self.emit(channel_name, body)
    
    def emit(self, channel_name, message, payload=None):
        """Emit the message to channel listeners."""
        logging.debug('Emitting event "%s": %s', channel_name, message)
        
        for listener in self.channels:
            try:
                listener.emit(message, channel_name)
            except IOError:
                # The stream is closed but the listener hasn't been removed.
                pass
            except AssertionError:
                # The response is finished.
                pass
            except RuntimeError:
                # ARRRR! :D
                pass
                
        if self.settings.get('mode', 'master') == 'master':
            if channel_name != 'sysmsg':
                self._update_status(channel_name, self.workers[channel_name].status())
            else:
                message = {
                    'command': message,
                    'payload': payload
                }   
            
            self.redis.publish('StatusBoard:' + channel_name, cPickle.dumps(message))
        else:
            if channel_name != 'sysmsg':
                self.statuses[channel_name] = cPickle.dumps(message)
        
class Channel(btheventsource.BTHEventStreamHandler):
    @tornado.web.asynchronous
    def get(self):
        StatusBoardApplication.add_listener('events', self)
        
    @tornado.web.asynchronous
    def post(self):
        StatusBoardApplication.add_listener('events', self)
                
# Routing table.
default_routes = [
    (r'/', StatusBoard.handlers.IndexHandler),
    (r'/people', StatusBoard.handlers.PeopleHandler),
    (r'/status/(.+?)', StatusBoard.handlers.StatusHandler),
    (r'/events', Channel)
]
            
def create_app(channels=None, config=None):
    """Instantiates and initializes the app according to config dict."""
    if channels == None or len(channels) == 0:
        raise RuntimeError('No channels defined.')
    
    if config == None:
        raise RuntimeError('No configuration given.')
        
    config['static_path'] = os.path.join(os.path.dirname(__file__), 'static')
    
    logging_config = {
        'format': "%(asctime)s %(name)s <%(levelname)s>: %(message)s",
        'level': logging.INFO
    }
    
    if config.get('debug', False):
        logging_config['level'] = logging.DEBUG
        
    logging.basicConfig(**logging_config)
    
    try:
        default_routes.append(
            (r'/(logo\.png)', tornado.web.StaticFileHandler, { 'path': config['logos_path'] }),
        )
        default_routes.append(
            (r'/(blanker_logo\.png)', tornado.web.StaticFileHandler, { 'path': config['logos_path'] }),
        )
    except KeyError:
        pass
        
    if config.get('theme', None):
        try:
            theme_path = os.path.join(config['themes_path'], config.get('theme'))
            default_routes.append(
                (r'/theme/(.+?)', StatusBoard.handlers.ThemeStaticFileHandler, { 'path': theme_path })
            )
        except KeyError:
            raise RuntimeError('Cannot switch theme without themes_path config setting.')
        
        config['theme_path'] = theme_path
        
    app = StatusBoardApplication(default_routes, **config)
    
    app.redis = brukva.Client(**config.get('redis', {}))
    app.redis.connect()
    
    for channel_name in channels:
        if isinstance(channels[channel_name], tuple) == False:
            worker_cls = channels[channel_name]
            worker_options = {}
            worker_interval = None
        else:
            worker_cls = channels[channel_name][0]
            worker_interval = channels[channel_name][1]
            try:
                worker_options = channels[channel_name][2]
            except IndexError:
                worker_options = {}
            
        worker = worker_cls(app, channel_name, interval=worker_interval, **worker_options)
        app.register_worker(channel_name, worker)            
    
    return app