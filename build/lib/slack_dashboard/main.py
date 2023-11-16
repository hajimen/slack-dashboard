import typing as ty
from datetime import datetime, timedelta
import time
import curses
import html
from urllib.error import URLError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import slack_dashboard.token_util as token_util
import slack_dashboard.channel_util as channel_util

MAX_ERROR = 3
ERROR_SPAN_TH = timedelta(seconds=30.)
INIT_SPAN = timedelta(days=7)


class WindowResizeException(Exception):
    pass


def main():
    while True:
        try:
            print(curses.wrapper(main_impl))
            break
        except WindowResizeException:
            pass


def main_impl(stdscr):
    n_error = 0
    last_error = None
    exit_msg = ''
    while True:
        try:
            s = Session(stdscr)
            s.connect()
        except URLError:
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
        except SlackApiError as e:
            exit_msg = str(e)
            break
        except KeyboardInterrupt:
            exit_msg = 'slack-dashboard exit by Ctrl+C.'
            break

    return exit_msg


class Session:
    def __init__(self, stdscr):
        self.last_t: ty.Optional[datetime] = None
        self.bot_profile_cache = {}
        self.sc: ty.Optional[WebClient] = None
        self.ch = None
        self.ch_name = None
        self.has_dateless_msg = False
        self.last_cn = ''
        self.last_un = ''

        curses.use_default_colors()

        curses.curs_set(0)
        full_h, full_w = stdscr.getmaxyx()
        webhook_win = curses.newwin(full_h - 2, full_w, 0, 0)
        webhook_win.scrollok(1)
        webhook_win.nodelay(True)
        status_win = curses.newwin(1, full_w, full_h - 2, 0)
        status_win.scrollok(1)
        status_win.refresh()
        prompt_win = curses.newwin(1, full_w, full_h - 1, 0)
        prompt_win.scrollok(1)
        self.stdscr = stdscr
        self.webhook_win, self.status_win, self.prompt_win = webhook_win, status_win, prompt_win

    def init_ch(self):
        cs = self.sc.users_conversations()

        self.ch = channel_util.load()
        if self.ch:
            for c in cs['channels']:
                if c['id'] == self.ch:
                    self.ch_name = c['name']
        else:
            available_ch_names = [c['name'] for c in cs['channels']]
            self.ch_name = channel_util.ask_name(self.webhook_win, self.status_win, self.prompt_win, available_ch_names)
            for c in cs['channels']:
                if c['name'] == self.ch_name:
                    self.ch = c['id']
                    channel_util.save_default(self.ch)
                    break

    def get_messages(self):
        last_ts = self.last_t.timestamp()
        ms = self.sc.conversations_history(
            oldest=str(last_ts),
            channel=self.ch)

        self.status_win.erase()
        self.status_win.addstr('Last connected: ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.status_win.noutrefresh()

        m_dict: dict[float, dict] = {}

        if 'messages' not in ms:
            return m_dict
        for m in ms['messages']:
            if m['type'] != 'message':
                continue
            ts = float(m['ts'])
            if abs(ts - last_ts) < 0.01:
                continue
            m['channel'] = self.ch
            m_dict[ts] = m

        return m_dict

    def connect(self):
        must_save_token = False
        token = token_util.load()
        if not token:
            token = token_util.ask(self.webhook_win, self.status_win, self.prompt_win)
            must_save_token = True

        self.sc = WebClient(token)
        self.init_ch()

        self.status_win.erase()
        self.webhook_win.erase()
        initial_erase = True
        self.webhook_win.addstr('No message in this week.')

        self.last_t = datetime.now() - INIT_SPAN

        while True:
            if self.last_t.day != datetime.now().day and self.has_dateless_msg:
                self.has_dateless_msg = False
                self.last_t = datetime.now() - INIT_SPAN

            m_dict = self.get_messages()
            if initial_erase and len(m_dict) > 0:
                self.webhook_win.erase()
                initial_erase = False
            for ts in sorted(m_dict.keys()):
                self.print_msg(m_dict[ts])
            self.webhook_win.noutrefresh()
            curses.doupdate()

            # now all OAuth scope verified
            if must_save_token:
                token_util.save_default(token)
                must_save_token = False

            for _ in range(100):
                time.sleep(0.1)
                k = self.webhook_win.getch()
                if k == curses.KEY_RESIZE:
                    time.sleep(1)  # wait tranquilizing
                    while self.webhook_win.getch() != -1:  # ignore other curses.KEY_RESIZE
                        pass
                    raise WindowResizeException()
                if k == 3:  # CTRL-C
                    raise KeyboardInterrupt('Ctrl-C')

    def print_msg(self, m):
        t = datetime.fromtimestamp(float(m['ts']))
        if self.last_t is not None and t.day != self.last_t.day:
            self.webhook_win.addstr('######### ' + t.strftime("%Y-%m-%d") + ' #########\n')
        self.last_t = t
        if 'user' in m:
            response = self.sc.users_info(user=m['user'])
            un = response['user']['profile']['real_name']
        elif 'bot_id' in m:
            if m['bot_id'] in self.bot_profile_cache:
                un = self.bot_profile_cache[m['bot_id']]
            else:
                r = self.sc.bots_info(bot=m['bot_id'])
                if 'bot' in r:
                    un = r['bot']['name']
                    self.bot_profile_cache[m['bot_id']] = un
                else:
                    un = 'unknown bot'
        if 'channel' in m:
            if m['channel'] != self.ch:
                return
            cn = self.ch_name
        else:
            cn = 'unknown'

        if t.day == datetime.now().day:
            self.has_dateless_msg = True
            t_str = t.strftime("%H:%M:%S")
        else:
            t_str = t.strftime("%Y-%m-%d %H:%M:%S")
        cn_str = '' if cn == self.last_cn else '@' + cn
        self.last_cn = cn
        self.webhook_win.addstr(cn_str + '(' + t_str + ')', curses.A_UNDERLINE)
        un_str = '' if un == self.last_un else '@' + '[' + un + ']'
        self.last_un = un
        self.webhook_win.addstr(un_str, curses.A_UNDERLINE | curses.A_BOLD)
        self.webhook_win.addstr(' - ' + html.unescape(m['text']) + '\n')


if __name__ == '__main__':
    main()
