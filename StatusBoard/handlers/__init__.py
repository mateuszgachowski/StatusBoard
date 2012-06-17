# -*- coding: utf-8 -*-
"""Request handlers."""

import tornado.web
import cPickle
import json
from StatusBoard.toolkit import SetEncoder
from hashlib import md5
import os
import sqlite3

class IndexHandler(tornado.web.RequestHandler):
    """Handler for root URL."""
    
    def get_template_path(self):
        if self.application.settings.get('theme', None):
            return self.application.settings['theme_path']
        else:
            return None
    
    def theme_url(self, path):
        settings = {
            'static_url_prefix': '/theme/',
            'static_path': self.application.settings['theme_path']
        }
        return ThemeStaticFileHandler.make_static_url(
            settings, path
        )
    
    def get(self):
        """Renders index template used to bootstrap the app."""
        if self.application.settings.get('theme', None):
            self.render('index.html', theme_url=self.theme_url)
        else:
            self.render('../templates/index.html')
        
class ThemeStaticFileHandler(tornado.web.StaticFileHandler):
    """Custom static file handler for theme files."""
    pass
        
class StatusHandler(tornado.web.RequestHandler):
    """Handler for getting worker status."""
    
    @tornado.web.asynchronous
    def get(self, channel_name):
        """Returns status of a specified worker."""
        if self.application.settings.get('mode', 'master') == 'master':
            status = self.application.redis.get('StatusBoard:status:' + channel_name, self._on_status)
        else:
            status = self.application.statuses.get(channel_name, None)
            self._on_status(status)
        
    def _on_status(self, status):
        if status is not None:
            try:
                status = cPickle.loads(status)
            except cPickle.UnpicklingError:
                status = None
                
        status = json.dumps(status, cls=SetEncoder)
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.write(status)
        self.finish()
            
    def post(self, channel_name):
        """Forces a worker identified by ``channel_name`` to refresh as if its
        timelimit was hit."""
        self.application.workers[channel_name].force_refresh()
        self.write('OK')
            
class PeopleHandler(tornado.web.RequestHandler):
    """Handler for list of people."""
    _h4x0r3d = dict()
    
    def get(self):
        """Returns list of people."""
        response = {}
        
        for i in range(len(self.application.settings['people'])):
            person = self.application.settings['people'][i]
            
            if self._h4x0r3d.has_key(person['gravatar_mail']):
                response[i] = self._h4x0r3d[person['gravatar_mail']]
            else:
                response[i] = {
                    'name': person['name'],
                    'gravatar_hash': md5(person['gravatar_mail'].lower()).hexdigest()
                }
            
        self.write(response)
        
    def post(self):
        """Hacks a person entry in people list.
        
        HOWTO:
        * POST /people body: person_idx=<person_idx>&name=<new_name>&gravatar_hash=<gravatar_hash>
        * Disco! :)"""
        try:
            current_person = self.application.settings['people'][int(self.get_argument('person_idx'))]
        except IndexError:
            raise tornado.web.HTTPError(400)
        
        new_person = {}
        
        try:
            new_person['name'] = self.get_argument('name')
        except:
            new_person['name'] = current_person['name']
        
        try:
            new_person['gravatar_hash'] = self.get_argument('gravatar_hash')
        except:
            new_person['gravatar_hash'] = md5(current_person['gravatar_mail'].lower()).hexdigest()
        
        if len(new_person) == 0:
            raise tornado.web.HTTPError(400)
            
        self._h4x0r3d[current_person['gravatar_mail']] = new_person
        self.application.emit('sysmsg', 'h4x0r_people', payload=self._h4x0r3d)
        self.write('Kaboom!')
        
    def delete(self):
        """Unhacks a person entry."""
        try:
            current_person = self.application.settings['people'][int(self.get_argument('person_idx'))]
        except IndexError:
            raise tornado.web.HTTPError(400)
            
        try:
            del(self._h4x0r3d[current_person['gravatar_mail']])
        except:
            raise tornado.web.HTTPError(400)
            
        self.application.emit('sysmsg', 'h4x0r_people', payload=self._h4x0r3d)
        self.write('Bummer.')