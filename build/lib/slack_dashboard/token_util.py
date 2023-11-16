'''
Stolen from https://github.com/regisb/slack-cli
'''
import os
import stat
import curses

import appdirs
from slack_dashboard import APP_NAME

TOKEN_PATH = os.path.join(appdirs.user_config_dir(APP_NAME), "slack_token")


def load():
    # Read from environment variable
    token = os.environ.get('SLACK_TOKEN')
    if token:
        return token

    # Read from local config file
    try:
        with open(TOKEN_PATH) as slack_token_file:
            return slack_token_file.read().strip()
    except IOError:
        return None


def ask(webhook_win, status_win, prompt_win):
    token = None
    curses.curs_set(1)
    while not token:
        message_main = """In order to interact with the Slack API, slack-dashboard requires a valid bot user OAuth token. To create and view your tokens, head over to:

    https://api.slack.com/authentication/token-types

The token should have these scopes:
- channels:history
- channels:read
- users:read

This message will only appear once. After the first run, the token will be stored in a local configuration file."""

        message_status = "Your bot user OAuth token: "
        webhook_win.clear()
        webhook_win.addstr(message_main)
        webhook_win.noutrefresh()

        status_win.erase()
        status_win.noutrefresh()

        prompt_win.erase()
        prompt_win.addstr(message_status)
        prompt_win.noutrefresh()

        curses.doupdate()

        def enter_is_terminate(x):
            if x == curses.KEY_ENTER or x == 10 or x == 13:
                x = 7
            return x

        from curses.textpad import Textbox
        tb = Textbox(prompt_win)
        tb.edit(enter_is_terminate)
        token = tb.gather()[len(message_status):]
    curses.curs_set(0)
    status_win.erase()
    status_win.noutrefresh()
    prompt_win.erase()
    prompt_win.noutrefresh()
    webhook_win.erase()
    webhook_win.noutrefresh()
    curses.doupdate()
    return token


def save_default(token):
    ensure_directory_exists(TOKEN_PATH)
    with open(TOKEN_PATH, "w") as slack_token_file:
        slack_token_file.write(token)
    os.chmod(TOKEN_PATH, stat.S_IREAD | stat.S_IWRITE)


def ensure_directory_exists(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
