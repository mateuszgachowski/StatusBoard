# -*- coding: utf-8 -*-
"""Twitter integration worker."""

import datetime
import feedparser
import logging
import StatusBoard.worker
import pytz
import tornado.httpclient

class FeedWorker(StatusBoard.worker.PeriodicWorker):
    _default_interval = 60 # 1 minute
    
    def _read_response(self, response):
        items = []
        
        feed = feedparser.parse(response.body)
        
        if 'bozo_exception' in feed:
            logging.error("FeedWorker (" + self._channel_name + "): couldn't read the feed.")
            logging.error("FeedWorker (" + self._channel_name + "): feedparser error: %s" % str(feed['bozo_exception']))
        else:
            for entry in feed['entries'][0:3]:
                entry_datetime = None
                for field in ['published_parsed', 'created_parsed', 'updated_parsed']:
                    try:
                        entry_datetime = entry[field]
                    except KeyError:
                        pass
                    else:
                        break
                        
                if entry_datetime is None:
                    entry_datetime = datetime.datetime.now(self.local_timezone)
                else:
                    entry_datetime = datetime.datetime(*(entry_datetime[0:6]), tzinfo=pytz.utc)
                    
                items.append({
                    'title': entry['title'],
                    'link': entry['link'],
                    'timedelta': self._format_timedelta(entry_datetime)
                })
                
        return items
    
    def warmup(self):
        logging.debug('FeedWorker (' + self._channel_name + '): Warming up.')
        http_client = tornado.httpclient.HTTPClient()
        
        response = http_client.fetch(self._options['url'])
        self._items = self._read_response(response)
        logging.debug('FeedWorker (' + self._channel_name + '): Warmed up.')
            
    def status(self):
        return { 'items': self._items }
        
    def _on_response(self, response):
        self._items = self._read_response(response)
        self._application.emit(self._channel_name, self.status())
        
    def _on_periodic_callback(self):
        logging.info('FeedWorker (' + self._channel_name + '): Timelimit hit.')
        http_client = tornado.httpclient.AsyncHTTPClient()
        
        http_client.fetch(self._options['url'], self._on_response)