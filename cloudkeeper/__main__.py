# coding: utf-8

# Copyright 2017 Hyeon Kim
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
# <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
# option. This file may not be copied, modified, or distributed
# except according to those terms.

from __future__ import print_function, unicode_literals, absolute_import
import sys
import time
import traceback
import binascii
from base64 import b64decode
if sys.version_info >= (3,):
    import pickle
else:
    import cPickle as pickle

from . import prompt
from .connection import IRCCloud


#
# Constants
#
DELAY = 30


def main():
    '''
    Main logic. Asks credentials to the user and tries to connect to the
    IRCCloud server infinitely.
    '''
    # Ask credentials to the user
    if len(sys.argv) > 2:
        print('Too many arguments have been supplied')
        sys.exit(1)
    elif len(sys.argv) < 2:
        # No credentials supplied
        data = prompt.ask()
    else:
        # Credentials have been supplied as a argument
        serialized = sys.argv[1]
        try:
            pickled = b64decode(serialized)
            data = pickle.loads(pickled)
        except (EOFError, ValueError, KeyError, binascii.Error, pickle.UnpicklingError) as e:
            print('Wrong arguments have been supplied ({})'.format(e))
            sys.exit(1)

    # Try to connect to the server infinitely
    while True:
        connection = IRCCloud()
        connection.auth(*data)
        try:
            connection.connect()
        except KeyboardInterrupt:
            print('\nGoodbye')
            sys.exit()
        except:
            print('\x1b[33m')
            print(traceback.format_exc())
            print('\x1b[0mDisconnected. Reconnecting in {} seconds.\n'.format(DELAY))
            time.sleep(DELAY)


if __name__ == '__main__':
    main()
