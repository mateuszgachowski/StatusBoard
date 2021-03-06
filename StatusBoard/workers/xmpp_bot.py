# -*- coding: utf-8 -*-
"""XMPP Bot."""

import StatusBoard.worker
import sleekxmpp
from copy import copy
import sqlite3
import json
import datetime
from functools import partial
import tornado.ioloop
from tornado.escape import xhtml_escape
import logging

class XMPPBot(StatusBoard.worker.BaseWorker):
    """XMPP Bot."""
    
    def __init__(self, *args, **kwargs):
        self._xmpp = None
        StatusBoard.worker.BaseWorker.__init__(self, *args, **kwargs)
        
    def _on_load_messages(self, response):
        for message in response:
            self._messages.append(json.loads(message))
            
        self._application._update_status(self._channel_name, self.status())
        logging.info('XMPPBot (' + self._channel_name + '): Warmed up.')
        
    def warmup(self):
        logging.info('XMPPBot (' + self._channel_name + '): Warming up.')
        self._messages = list()
        
        self._application.redis.lrange('StatusBoard:xmpp:' + self._channel_name,
            0, 4, self._on_load_messages
        )
            
    def status(self):
        response = {}
        i = 0
        for message in self._messages[0:5]:
            response[i] = self._messages[i]
            i += 1
            
        return response
        
    def start(self):
        self._xmpp = sleekxmpp.ClientXMPP(
            self._options['jid'],
            self._options['password']
        )
        
        self._xmpp.connect((
            self._options['server'],
            self._options['port']
        ))
        
        self._xmpp.add_event_handler("session_start", self._on_xmpp_session_start)
        self._xmpp.add_event_handler("message", self._on_xmpp_message)
        
        self._xmpp.process()
        
    def _handle_client_mode(self, msg, *args):
        if len(args) == 0:
            msg.reply('client_mode: mode project,project').send()
            return
            
        if 'redmine_channel' not in self._options:
            msg.reply('client_mode: this bot is not connected to Redmine').send()
            return
        
        mode = args[0]
        
        projects = None
        try:
            projects = args[1].split(',')
        except:
            pass
        
        if mode == 'on':
            if projects == None:
                msg.reply('client_mode: mode project,project').send()
                return
            
            self._application.workers[self._options['redmine_channel']].client_mode('on', projects=projects)
        elif mode == 'off':
            self._application.workers[self._options['redmine_channel']].client_mode('off', projects=projects)
        else:
            msg.reply('client_mode: mode not found: ' + mode).send()
        
    def _process_command(self, msg):
        command = msg['body'][1:].split(' ')
        
        handler = getattr(self, '_handle_' + command[0], None)
        if handler == None:
            msg.reply('%s: command not found' % (command[0], )).send()
        else:
            args = []
            if len(command) > 1:
                args = command[1:]
            handler(msg, *args)
        
    def _process_xmpp_message(self, msg):
        """Processes and emits the message.
        
        This method does the actual processing and is called automagically from
        self._on_xmpp_message()."""
        if msg['body'].startswith('/') == True:
            self._process_command(msg)
        else:
            author = str(msg['from']).encode('utf-8').split('/')[0]
            person_idx = self._person_idx('jid', author)
            
            if person_idx != None:
                message = {
                    'person': person_idx,
                    'message': xhtml_escape(msg['body'])
                }
                
                self._messages = [ message ] + self._messages
                if len(self._messages) > 5:
                    self._messages.pop()
                    
                self._application.redis.lpush('StatusBoard:xmpp:' + self._channel_name,
                    json.dumps(message)
                )
                                
                self._application.emit(self._channel_name, message)

    def _on_xmpp_session_start(self, event):
        """Handles XMPP session start event."""
        self._xmpp.send_presence()
        self._xmpp.get_roster()

    def _on_xmpp_message(self, msg):
        """Handles XMPP message event."""
        if msg['type'] in ('chat', 'normal'):
            tornado.ioloop.IOLoop.instance().add_callback(partial(self._process_xmpp_message, msg))