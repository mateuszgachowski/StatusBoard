StatusBoard
=

StatusBoard is a Tornado application we use to display a Web page with info about things that are going on around our office.

Channels and workers
-

The app uses SSE (wrapped with [BTHEventSource](https://github.com/tomekwojcik/BTHEventSource)) to communicate with browsers.

The `config.py.default` file defines a single channel for Pinger. `channel_name` will be used as an SSE event name.

Workers provide data for channels. There are two types of workers:

1. `StatusBoard.worker.PeriodicWorker` - invoked periodically at a given interval,
1. `StatusBoard.worker.ScheduledWorker` - one-shot worker invoked after scheduling.

There are six workers in the box:

1. `StatusBoard.workers.FeedWorker` - fetches and parses feeds (RSS, Atom, CDF),
1. `StatusBoard.workers.PingerWorker` - pings computers defined in config to determine number of present and absent people,
1. `StatusBoard.workers.TwitterWorker` - fetches user's tweets,
1. `StatusBoard.workers.RedmineWorker` - connects the app to Redmine instance to provide info about projects status,
1. `StatusBoard.workers.YahooWeatherWorker` - fetches weather info from Yahoo! Weather,
1. `StatusBoard.workers.XMPPBot` - controls XMPP bot that feeds _Breaking News_ section.

The config.py file
-
`config.py` contains a dictionary that'll be loaded by `status_board` and passed to Tornado app. It's the place to provide app's config. For more info about default fields see Tornado.

App-specific config dict fields:

+ `people` - list of dicts containing people definition. Mandatory fields are `name` and `gravatar_mail`. `ip` is used by PingerWorker. `jid` is used by XMPPBot, `redmine_mail` by RedmineWorker and workers will fall back to `gravatar_mail` automagically if their fields aren't present.
+ `redis` - Redis DB connection details.
+ `theme` - theme to use. If it's not set then default theme is used.

Channel definitions
-

The config file contains a dict of channel definitions. The syntax is:

```
channels = {
    '<channel_name>': ( WorkerClass, <interval>, [settings_dict] )
}
```

`interval` is in seconds. Pass `None` to use worker's default interval.
`settings_dict` contains worker-specific settings.

`config.py.default` file contains dummy settings dicts for all the built-in workers. Note that PingerWorker doesn't require any additional settings.

Themes
-

`app_config['themes_path']` allows you to define a path to themes library. `config.py` sets `themes_path` to the directory where the file is located. Feel free to change the path.

Currently the app comes bundled with two themes - default (which will be used if you skip `theme` field in `app_config` dict) and `bootstrapped` (based on Twitter's Bootstrap).


Logos
-
Built-in theme allows you to set custom logos. If you wish to do that place files `logo.png` and `blanker_logo.png` in `app_config['logo_path']`. `config.py` sets `logo_path` to the directory where the file is located. Feel free to change the path.

Use a 187px x 119px image for `logo.png`. `blanker_logo.png` will be centered in the viewport automatically.

Master/slave mode
-

StatusBoard can work in two modes - master or slave.

Master instance runs workers and updates Redis DB according to their status (on warmup) and events they emit.
Slave instance listens to notifications posted by master (using Redis PubSub) and emits events to its listeners.

Use of this architecture and Redis PubSub technology allows you to spawn one master and many slaves thus improving number of simultaneous connections handled by the app.

By default the app starts in master mode. To start a slave instance use `-s` switch. Note that you should take care to start slaves after the master.

Screens
-

![Screen 01](http://weebystudio.com/sb/01.jpg)

![Screen 02](http://weebystudio.com/sb/02.jpg)

![Screen 03](http://weebystudio.com/sb/03.jpg)

Credits
-
Weather state icons: http://vclouds.deviantart.com/art/VClouds-Weather-Icons-179152045 (CC BY-NC-SA 3.0)

Installation, setup and running
-
1. Create a virtualenv, activate it, clone the repo and cd to it,
1. `python setup.py install` (requires distribute)
1. `cp config.py.default config.py`
1. `vim config.py`
1. `status_board`
1. Point the browser to app's URL (see `status_board --help` for info).
1. Sit down and watch the magic happen.
1. Profit?

License
-
BSD License