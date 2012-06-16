# -*- coding: utf-8 -*-
"""Twitter integration worker."""

import StatusBoard.worker
import tornado.httpclient
import json
import logging
import datetime
import math
import time
import pytz

DEFAULT_TIMEOUT = 600 # 10 minutes

class TwitterWorker(StatusBoard.worker.ScheduledWorker):
    """Twitter integration worker."""
    timeout = DEFAULT_TIMEOUT
    
    _base_url = 'http://api.twitter.com/1/statuses/user_timeline.json?screen_name='
        
    def _is_rate_limit_exceeded(self, response):
        if response.code == 400:
            try:
                assert response.headers['X-RateLimit-Remaining'] == "0"
            except (KeyError, AssertionError):
                return False
            else:
                return True
            
        return False
        
    def _throttled_timeout(self, response):
        if response.code == 400:
            try:
                reset_timestamp = int(response.headers['X-RateLimit-Reset'])
            except (KeyError, TypeError, ValueError):
                return DEFAULT_TIMEOUT
                
            reset_datetime = datetime.datetime.fromtimestamp(reset_timestamp, pytz.utc)
            reset_datetime = reset_datetime.astimezone(self.local_timezone)
            reset_timedelta = reset_datetime - datetime.datetime.now(self.local_timezone)
            
            if reset_timedelta.seconds > 0:
                logging.debug('Seconds until rate reset: ' + str(reset_timedelta.seconds))
                return reset_timedelta.seconds + 60
            else:
                return DEFAULT_TIMEOUT
        
    def _twitter_request(self):
        return self._base_url + self._application.settings['twitter_username']
    
    def _parse_tweet(self, text):
        return text
    
    def _read_response(self, response):
        tweets = []
        
        try:
            data = json.loads(response.body)
        except (TypeError, ValueError):
            logging.error('TwitterWorker: Failed to decode response.')
            logging.debug('TwitterWorker: Response was: ' + str(response.body))
        else:
            if response.code != 200:
                logging.error('TwitterWorker: Got status: ' + str(response.code) + '.')
                if 'error' in data:
                    logging.error('TwitterWorker: Got error: "' + data['error'] + '".')
                
                if 'errors' in data:
                    for error in data['errors']:
                        logging.error('TwitterWorker: Got error: "' + error['message'] + '".')
            else:
                for tweet in data[0:5]:
                    tweet_datetime = datetime.datetime(*(time.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y")[0:6]),
                                           tzinfo=pytz.utc)
                    tweets.append({
                        'id': tweet['id_str'],
                        'text': self._parse_tweet(tweet['text']),
                        'timedelta': self._format_timedelta(tweet_datetime)
                    })
                
        return tweets
        
    def _on_response(self, response):
        if self._is_rate_limit_exceeded(response) == True:
            logging.error('TwitterWorker: Rate limit exceeded. Tweaking timeout.')
            self.timeout = self._throttled_timeout(response)
        else:
            self.timeout = DEFAULT_TIMEOUT
            self._tweets = self._read_response(response)
            self._application.emit('twitter', self.status())
            
        self.start()
    
    def warmup(self):
        logging.debug('TwitterWorker: Warming up.')
        http_client = tornado.httpclient.HTTPClient()
        
        try:
            response = http_client.fetch(self._twitter_request())
        except tornado.httpclient.HTTPError, exc:
            if self._is_rate_limit_exceeded(exc.response) == True:
                logging.error('TwitterWorker: Rate limit exceeded. Tweaking timeout.')
                self.timeout = self._throttled_timeout(exc.response)
            else:
                raise
            
            self._tweets = []
        else:
            self._tweets = self._read_response(response)
            
        logging.debug('TwitterWorker: Warmed up.')
        
    def status(self):
        return { 'tweets': self._tweets }
        
    def _on_timeout(self):
        logging.info('TwitterWorker: Timelimit hit.')
        
        self.stop()
        http_client = tornado.httpclient.AsyncHTTPClient()
        
        http_client.fetch(self._twitter_request(), self._on_response)