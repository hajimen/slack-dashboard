import os
from datetime import datetime, timedelta
from dateutil.parser import parse
import time
import slack_dashboard.token_util as token_util
from slackclient import SlackClient
from slackclient.server import SlackConnectionError
import curses
import appdirs

MAX_ERROR = 3
ERROR_SPAN_TH = timedelta(seconds=30.)

APP_NAME = 'slack-dashboard'
LMR_PATH = os.path.join(appdirs.user_config_dir(APP_NAME), "last_msg_received")


def main():
    print(curses.wrapper(main_impl))


def main_impl(stdscr):
    n_error = 0
    last_error = None
    exit_msg = ''
    while True:
        try:
            s = Session(stdscr)
            exit_msg = s.connect()
            break
        except (SlackConnectionError, TimeoutError):
            t = datetime.now()
            if last_error is not None:
                if t - last_error < ERROR_SPAN_TH:
                    n_error += 1
                    if n_error > MAX_ERROR:
                        exit_msg = 'Network connection is unstable or lost.'
                        break
                else:
                    n_error = 0
            last_error = t
            time.sleep(10.)
        except KeyboardInterrupt:
            exit_msg = 'slack-dashboard exit by Ctrl+C.'
            break

    return exit_msg


class Session:
    def __init__(self, stdscr):
        self.last_t = None
        self.bot_profile_cache = {}
        self.sc = None

        curses.curs_set(0)
        full_h, full_w = stdscr.getmaxyx()
        webhook_win = curses.newwin(full_h - 2, full_w, 0, 0)
        webhook_win.scrollok(1)
        status_win = curses.newwin(1, full_w, full_h - 2, 0)
        status_win.scrollok(1)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        status_win.bkgd(' ', curses.color_pair(1))
        status_win.refresh()
        prompt_win = curses.newwin(1, full_w, full_h - 1, 0)
        prompt_win.scrollok(1)
        self.stdscr = stdscr
        self.webhook_win, self.status_win, self.prompt_win = webhook_win, status_win, prompt_win

    def set_last_msg_received(self, t):
        d = os.path.dirname(LMR_PATH)
        if not os.path.exists(d):
            os.makedirs(d)
        with open(LMR_PATH, 'w') as f:
            f.write(str(t))

    def get_last_msg_received(self):
        if not os.path.isfile(LMR_PATH):
            t = datetime.now()
            self.set_last_msg_received(t)
            return t
        with open(LMR_PATH, 'r') as f:
            s = f.read()
        return parse(s)

    def connect(self):
        must_save_token = False
        token = token_util.load()
        if not token:
            token = token_util.ask(self.webhook_win, self.status_win, self.prompt_win)
            must_save_token = True

        self.sc = SlackClient(token)

        cs = self.sc.api_call('users.conversations')
        m_dict = {}

        self.last_t = self.get_last_msg_received()
        last_ts = self.last_t.timestamp()
        for c in cs['channels']:
            cid = c['id']
            ms = self.sc.api_call(
                'channels.history',
                oldest=str(last_ts),
                channel=cid)
            if not ('messages' in ms):
                continue
            for m in ms['messages']:
                if m['type'] != 'message':
                    continue
                ts = float(m['ts'])
                if abs(ts - last_ts) < 0.01:
                    continue
                m['channel'] = cid
                m_dict[ts] = m

        if self.sc.rtm_connect():
            self.status_win.erase()
            self.status_win.refresh()
            self.webhook_win.nodelay(True)
            self.webhook_win.erase()
            self.webhook_win.refresh()
            if must_save_token:
                token_util.save_default(token)
                must_save_token = False
            for ts in sorted(m_dict.keys()):
                self.print_msg(m_dict[ts])
            self.webhook_win.refresh()
            while True:
                ms = self.sc.rtm_read()
                self.status_win.erase()
                self.status_win.addstr('Last connected: ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.status_win.refresh()
                for m in ms:
                    self.print_msg(m)
                self.webhook_win.refresh()
                for _ in range(100):
                    time.sleep(0.1)
                    k = self.webhook_win.getch()
                    if k == curses.KEY_RESIZE:
                        full_h, full_w = self.stdscr.getmaxyx()
                        self.webhook_win.resize(full_h - 2, full_w)
                        self.webhook_win.refresh()
                        self.status_win.resize(1, full_w)
                        self.status_win.mvwin(full_h - 2, 0)
                        self.status_win.refresh()
                        self.prompt_win.resize(1, full_w)
                        self.prompt_win.mvwin(full_h - 1, 0)
                        self.prompt_win.refresh()
                    if k == 3:  # CTRL-C
                        raise KeyboardInterrupt('Ctrl-C')
        else:
            return "Connection Failed, invalid token?"

    def print_msg(self, m):
        if 'bot_profile' in m:
            bp = m['bot_profile']
            self.bot_profile_cache[bp['id']] = bp['name']
        if m['type'] == 'message':
            t = datetime.fromtimestamp(float(m['ts']))
            if self.last_t is not None and t.day != self.last_t.day:
                self.webhook_win.addstr('######### ' + t.strftime("%Y-%m-%d") + ' #########\n')
            self.last_t = t
            if 'user' in m:
                un = self.sc.server.users.get(m['user']).real_name
            elif 'bot_id' in m:
                if m['bot_id'] in self.bot_profile_cache:
                    un = self.bot_profile_cache[m['bot_id']]
                else:
                    r = self.sc.api_call('bots.info', bot=m['bot_id'])
                    if 'bot' in r:
                        un = r['bot']['name']
                        self.bot_profile_cache[m['bot_id']] = un
                    else:
                        un = 'unknown bot'
            if 'channel' in m:
                cn = self.sc.server.channels.find(m['channel']).name
            else:
                cn = 'unknown'
            self.webhook_win.addstr('@' + cn + '(' + t.strftime("%Y-%m-%d %H:%M:%S") + ')', curses.A_UNDERLINE)
            self.webhook_win.addstr('[' + un + ']', curses.A_UNDERLINE | curses.A_BOLD)
            self.webhook_win.addstr(' - ' + m['text'] + '\n')
            self.set_last_msg_received(t)
