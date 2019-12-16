import os
from datetime import datetime, timedelta
from dateutil.parser import parse
import time
import slack_dashboard.token_util as token_util
from slackclient import SlackClient
from slackclient.server import SlackConnectionError
from colored import attr
import appdirs

MAX_ERROR = 3
ERROR_SPAN_TH = timedelta(seconds=30.)

APP_NAME = 'slack-dashboard'
LMR_PATH = os.path.join(appdirs.user_config_dir(APP_NAME), "last_msg_received")


def main():
    n_error = 0
    last_error = None
    while True:
        try:
            s = Session()
            s.connect()
            break
        except SlackConnectionError:
            t = datetime.now()
            if last_error is not None:
                if t - last_error > ERROR_SPAN_TH:
                    n_error += 1
                    if n_error > MAX_ERROR:
                        print('Network connection is unstable or lost.')
                        return
                else:
                    n_error = 0
            last_error = t
            time.sleep(10.)
        except KeyboardInterrupt:
            print('Exit by Ctrl+C.')
            return

class Session:
    def __init__(self):
        self.last_t = None
        self.bot_profile_cache = {}
        self.sc = None

    def set_last_msg_received(self, t: datetime):
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
            token = token_util.ask()
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
            if must_save_token:
                token_util.save_default(token)
                must_save_token = False
            for ts in sorted(m_dict.keys()):
                self.print_msg(m_dict[ts])
            while True:
                ms = self.sc.rtm_read()
                for m in ms:
                    self.print_msg(m)
                time.sleep(10.)
        else:
            print("Connection Failed, invalid token?")

    def print_msg(self, m):
        if 'bot_profile' in m:
            bp = m['bot_profile']
            self.bot_profile_cache[bp['id']] = bp['name']
        if m['type'] == 'message':
            t = datetime.fromtimestamp(float(m['ts']))
            if self.last_t is not None and t.day != self.last_t.day:
                print('######### ' + t.strftime("%Y-%m-%d") + ' #########')
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
            print(attr('underlined') + '@' + cn + '(' + t.strftime("%Y-%m-%d %H:%M:%S") + ')' \
                    + attr('bold') + '[' + un + ']' + attr('reset') + ' - ' + m['text'])
            self.set_last_msg_received(t)

if __name__ == "__main__":
    main()
