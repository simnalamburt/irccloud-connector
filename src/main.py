# Copyright 2017 Hyeon Kim
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
# <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
# option. This file may not be copied, modified, or distributed
# except according to those terms.

from __future__ import print_function, unicode_literals
import json
import sys
import time
import traceback
import random
import string
from getpass import getpass
if sys.version_info >= (3,):
    from configparser import SafeConfigParser
    import _thread as thread
else:
    from ConfigParser import SafeConfigParser
    import thread
    input = raw_input

import requests
from websocket import create_connection


DELAY = 30


class IRCCloud(object):
    def __init__(self):
        self.session = ''
        self.uri = 'https://www.irccloud.com/chat/login'
        self.uri_formauth = 'https://www.irccloud.com/chat/auth-formtoken'
        self.origin = 'https://www.irccloud.com'
        self.wss = 'wss://api.irccloud.com/websocket/' + random.choice(string.digits)
        self.last = 0
        self.timeout = 120
        self.config = SafeConfigParser()

    def connect(self):
        for line in self.create(self.session):
            if self.last == 0:
                # Just started..
                thread.start_new_thread(self.check, ())
            self.last = self.current_time()
            self.parseline(line)

    def reload_config(self):
        self.config = SafeConfigParser()
        self.config.read('secret.ini')

    def auth(self):
        try:
            # Load (or reload) configuration file
            self.reload_config()

            # Check if we have any valid configuration. If we do, load it!
            good_config = True
            if self.config.has_section('auth'):
                if self.config.has_option('auth', 'email') and self.config.has_option('auth', 'password'):
                    user_email    = self.config.get('auth', 'email')
                    user_password = self.config.get('auth', 'password')
                else:
                    good_config = False
            else:
                good_config = False

            # No valid configuration? No problem!
            if good_config:
                print('Loaded configuration')
            else:
                print('No configuration (secret.ini) detected (or configuration corrupted)!')
                user_email    = input('Enter your IRCCloud email: ')
                user_password = getpass('Enter your IRCCloud password: ')

                # Commit to configuration
                if not self.config.has_section('auth'):
                    self.config.add_section('auth')
                self.config.set('auth', 'email', user_email)
                self.config.set('auth', 'password', user_password)

                # Attempt to save configuration
                print('Saving configuration ... ', end='', flush=True)
                try:
                    self.configfh = open('secret.ini', 'w')
                    self.config.write(self.configfh)
                    self.configfh.close()
                    print('Done')
                    self.reload_config()
                except:
                    print(traceback.format_exc())
                    print('Failed!')
                    try:
                        self.configfh.close()
                    except:
                        pass

            # New form-auth API needs token to prevent CSRF attacks
            print('Authenticating ... ', end='', flush=True)
            token = requests.post(self.uri_formauth, headers={'content-length': '0'}).json()['token']
            data = {'email': user_email, 'password': user_password, 'token': token}
            headers = {'x-auth-formtoken': token}
            resp = requests.post(self.uri, data=data, headers=headers)
            data = json.loads(resp.text)
            if 'session' not in data:
                print('[error] Wrong email/password combination. Exiting.')
                sys.exit()
            self.session = data['session']
            print('Done')
        except requests.exceptions.ConnectionError:
            print('Failed!')
            raise Exception('Failed to connect')

    def create(self, session):
        h = ['Cookie: session=%s' % session]
        self.ws = create_connection(self.wss, header=h, origin=self.origin)
        print('Connection created.')
        while True:
            msg = self.ws.recv()
            if msg:
                yield json.loads(msg)

    def parseline(self, line):
        def oob_include(l):
            h = {'Cookie': 'session=%s' % self.session, 'Accept-Encoding': 'gzip'}
            requests.get(self.origin + l['url'], headers=h).json()

        try:
            locals()[line['type']](line)
        except KeyError:
            pass

    def diff(self, time):
        return int(int(time) - int(self.last))

    def current_time(self):
        return int(time.time())

    def check(self):
        while True:
            time.sleep(5)
            diff = self.diff(self.current_time())
            if diff > self.timeout and self.last != 0:
                print('[error] Connection timed out...')
                if hasattr(self, 'ws'):
                    self.ws.close()
                return


if __name__ == '__main__':
    try:
        while True:
            try:
                feed = IRCCloud()
                feed.auth()
                feed.connect()
            except KeyboardInterrupt:
                sys.exit()
            except:
                print(traceback.format_exc())
                print('Disconnected. Reconnecting in {} seconds.\n'.format(DELAY))
                time.sleep(DELAY)
                continue
    except KeyboardInterrupt:
        sys.exit()
