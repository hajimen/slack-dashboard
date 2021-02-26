# Slack dashboard

You shouldn't look at any notifications when you don't want to respond them.
Switch your life from notification to dashboard. A dashboard doesn't disturb you worthlessly. 

## Prerequisites

In Windows, you need `windows-curses` or something. But `windows-curses` lacks resize feature.

Works on Python 3.4 and later. In other words, works on hacked Kobo Touch.

You need a legacy token. You don't have it? Sorry, it's too late.

## How to use

Just execute `slack-dashboard` on your shell.

## Main feature

Shows a channel of an workspace of a legacy token.

## Main non-feature

This isn't a terminal. It is a dashboard. Cannot send any message.

No operation. You just look at it. Exit by Ctrl-C.

No kindness. When you need to change the Slack token or channel, remove old configuration files.
`appdirs` decides the directory. In Ubuntu, `~/.config/slack-dashboard'.

No quality. This is just a hack for myself, my life.

## My use

Monitoring of an online service, [Zygomatic Color](https://zm-color.com/).

## Version history

### 0.1.1

Fix: Slack API stopped to accept ['channels.history'](https://api.slack.com/methods/channels.history) call.

Change: Now slack-dashboard listen on just a channel, not an workspace whole.

### 0.1.0

Initial version.

## License

Copyright 2020 Hajime Nakazato

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
