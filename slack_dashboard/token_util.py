'''
Stolen from https://github.com/regisb/slack-cli
'''
import json
import os
import stat
import curses

import appdirs

APP_NAME = 'slack-dashboard'


TOKEN_PATH = os.path.join(appdirs.user_config_dir(APP_NAME), "slack_token")
TEAMS_PATH = os.path.join(appdirs.user_config_dir(APP_NAME), "teams.json")


def load(team=None):
    # Read from environment variable
    token = os.environ.get('SLACK_TOKEN')
    if token:
        return token

    # Read from local config file
    if team:
        try:
            with open(TEAMS_PATH) as teams_file:
                teams = json.load(teams_file)
            if team in teams:
                token = teams[team]["token"]
                save_default(token)
                return token
        except IOError:
            pass
    else:
        try:
            with open(TOKEN_PATH) as slack_token_file:
                return slack_token_file.read().strip()
        except IOError:
            pass


def ask(webhook_win, status_win, prompt_win, team=None):
    token = None
    curses.curs_set(1)
    while not token:
        message_main = """In order to interact with the Slack API, slack-cli requires a valid Slack API token. To create and view your tokens, head over to:

    https://api.slack.com/custom-integrations/legacy-tokens

This message will only appear once. After the first run, the Slack API token will be stored in a local configuration file."""

        message_status = "Your Slack API token{}: ".format(" for the " + team + " team" if team else "")
        webhook_win.clear()
        webhook_win.addstr(message_main)
        status_win.clear()
        status_win.addstr(message_status)
        webhook_win.refresh()
        status_win.refresh()
        prompt_win.erase()
        prompt_win.refresh()

        def enter_is_terminate(x):
            if x == 10:
                x = 7
            return x

        from curses.textpad import Textbox
        tb = Textbox(prompt_win)
        tb.edit(enter_is_terminate)
        token = tb.gather()
    curses.curs_set(0)
    status_win.erase()
    status_win.refresh()
    prompt_win.erase()
    prompt_win.refresh()
    webhook_win.erase()
    webhook_win.refresh()
    return token


def save(token, team):
    save_default(token)
    save_team(token, team)


def save_default(token):
    ensure_directory_exists(TOKEN_PATH)
    with open(TOKEN_PATH, "w") as slack_token_file:
        slack_token_file.write(token)
    os.chmod(TOKEN_PATH, stat.S_IREAD | stat.S_IWRITE)


def save_team(token, team):
    ensure_directory_exists(TOKEN_PATH)
    teams = {}
    if os.path.exists(TEAMS_PATH):
        with open(TEAMS_PATH) as teams_file:
            teams = json.load(teams_file)
    teams[team] = {"token": token}
    with open(TEAMS_PATH, 'w') as teams_file:
        json.dump(teams, teams_file, sort_keys=True, indent=4)
    os.chmod(TEAMS_PATH, stat.S_IREAD | stat.S_IWRITE)


def ensure_directory_exists(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
