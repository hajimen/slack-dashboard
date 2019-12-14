# from pprint import pprint
from datetime import datetime
import time
import slack_dashboard.token_util as token_util
from slackclient import SlackClient
from colored import attr

def main():
    must_save_token = False
    token = token_util.load()
    if not token:
        token = token_util.ask()
        must_save_token = True

    sc = SlackClient(token)
    bot_profile_cache = {}

    if sc.rtm_connect():
        last_t = None
        if must_save_token:
            token_util.save_default(token)
            must_save_token = False
        while True:
            ms = sc.rtm_read()
            # if len(ms) > 0:
            #     pprint(ms)
            for m in ms:
                if 'bot_profile' in m:
                    bp = m['bot_profile']
                    bot_profile_cache[bp['id']] = bp['name']
                if m['type'] == 'message':
                    t = datetime.fromtimestamp(float(m['ts']))
                    if last_t is not None and t.day != last_t.day:
                        print('######### ' + t.strftime("%Y-%m-%d") + ' #########')
                    last_t = t
                    if 'user' in m:
                        un = sc.server.users.get(m['user']).real_name
                    elif 'bot_id' in m:
                        un = bot_profile_cache[m['bot_id']]
                    cn = sc.server.channels.find(m['channel']).name
                    print(attr('underlined') + '@' + cn + '(' + t.strftime("%Y-%m-%d %H:%M:%S") + ')' \
                         + attr('bold') + '[' + un + ']' + attr('reset') + ' - ' + m['text'])
            time.sleep(10.)
    else:
        print("Connection Failed, invalid token?")


if __name__ == "__main__":
    main()
