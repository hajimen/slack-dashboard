import os
import stat
import curses

import appdirs

APP_NAME = 'slack-dashboard'


CHANNEL_PATH = os.path.join(appdirs.user_config_dir(APP_NAME), "slack_channel")


def load():
    # Read from environment variable
    ch = os.environ.get('SLACK_CHANNEL')
    if ch:
        return ch

    # Read from local config file
    try:
        with open(CHANNEL_PATH) as slack_ch_file:
            return slack_ch_file.read().strip()
    except IOError:
        return None


def ask_name(webhook_win, status_win, prompt_win, available_ch_names):
    acn = ', '.join(['#' + x for x in available_ch_names])
    message_main = """Which channel do you listen? Type 'foo' of the channel name '#foo'.

Available channels: """ + acn + "\n\nThis message will only appear once. After the first run, the name will be stored in a local configuration file."

    ch = None
    curses.curs_set(1)
    while (not ch) or not (ch in available_ch_names):
        message_status = "Channel name which you listen: #"
        webhook_win.clear()
        webhook_win.addstr(message_main)
        status_win.clear()
        status_win.addstr(message_status)
        webhook_win.refresh()
        status_win.refresh()
        prompt_win.erase()
        prompt_win.refresh()

        def enter_is_terminate(x):
            if x == curses.KEY_ENTER or x == 10 or x == 13:
                x = 7
            return x

        from curses.textpad import Textbox
        tb = Textbox(prompt_win)
        tb.edit(enter_is_terminate)
        ch = tb.gather().strip()
    curses.curs_set(0)
    status_win.erase()
    status_win.refresh()
    prompt_win.erase()
    prompt_win.refresh()
    webhook_win.erase()
    webhook_win.refresh()
    return ch


def save_default(ch):
    ensure_directory_exists(CHANNEL_PATH)
    with open(CHANNEL_PATH, "w") as slack_ch_file:
        slack_ch_file.write(ch)
    os.chmod(CHANNEL_PATH, stat.S_IREAD | stat.S_IWRITE)


def ensure_directory_exists(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
