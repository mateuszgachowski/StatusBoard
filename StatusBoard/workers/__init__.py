# -*- coding: utf-8 -*-
import StatusBoard.worker
import datetime

class DummyPeriodicWorker(StatusBoard.worker.PeriodicWorker):
    def status(self):
        return None
        
    def _on_periodic_callback(self):
        self._application.emit(self._channel_name, 'DummyPeriodicWorker')
        
class DummyScheduledWorker(StatusBoard.worker.ScheduledWorker):
    def status(self):
        return None
        
    def _on_timeout(self):
        self.stop()
        self._application.emit(self._channel_name, 'DummyScheduledWorker')
        self.start()

from StatusBoard.workers.pinger import PingerWorker
from StatusBoard.workers.xmpp_bot import XMPPBot
from StatusBoard.workers.redmine import RedmineWorker
from StatusBoard.workers.yahoo_weather import YahooWeatherWorker
from StatusBoard.workers.twitter import TwitterWorker
from StatusBoard.workers.feed import FeedWorker