#!/usr/bin/env python
"""
admin.py - Phenny Admin Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import os
import re
import subprocess

from modules import reload

def check_return(command):
    try:
        subprocess.check_call(command)
        return True
    except subprocess.CalledProcessError:
        return False

def get_output(command):
    try:
        return subprocess.check_output(command)
    except subprocess.CalledProcessError:
        return None

def check_signature(message, signature):
    return check_return(['./ssh/verify-msg.sh'] + message + [signature])

def upgrade(phenny, input):
    """Request remote upgrade using a cryptographic signature"""
    commit, signature = input.group(1), input.group(2)

    # check if we have a cryptographic public key

    if not os.path.isfile(os.path.expanduser('~/.phenny/id_rsa.pub')):
        phenny.reply('This instance has no cryptographic public key.')
        return

    # limit input space

    if not re.fullmatch('[0-9a-f]{40}', commit):
        phenny.reply('Invalid format: commit hash')
        return

    if not re.fullmatch('[A-Za-z0-9+/=]{172}', signature):
        phenny.reply('Invalid format: signature')
        return

    # check cryptographic signature

    if not check_signature(['.upgrade', commit], signature):
        phenny.reply('Signature is invalid')
        return

    phenny.reply('Signature is valid')
    os.system('git fetch --all')

    # ensure signature is not used twice

    current = get_output(['git', 'rev-parse', 'HEAD'])
    history = get_output(['git', 'rev-list', commit])

    if current not in history:
        phenny.reply('Specified commit must be newer than current.')
        return

    # deal with potentially dirty workspace

    if not check_return(['git', 'rebase', '--autostash', commit]):
        phenny.reply('Failed to rebase & autostash changes')
        return

    reload.restart(phenny)
upgrade.rule = r'\.upgrade (\S+) (\S+)'

def join(phenny, input): 
    """Join the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    if input.admin: 
        channel, key = input.group(1), input.group(2)
        phenny.proto.join(channel, key)
join.rule = r'\.join (#\S+)(?: *(\S+))?'
join.priority = 'low'
join.example = '.join #example or .join #example key'

def autojoin(phenny, input): 
    """Join the specified channel when invited by an admin."""
    if input.admin: 
        channel = input.group(1)
        phenny.proto.join(channel)
autojoin.event = 'INVITE'
autojoin.rule = r'(.*)'

def part(phenny, input): 
    """Part the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    if input.admin: 
        phenny.proto.part(input.group(2))
part.rule = (['part'], r'(#\S+)')
part.priority = 'low'
part.example = '.part #example'

def quit(phenny, input): 
    """Quit from the server. This is an owner-only command."""
    # Can only be done in privmsg by the owner
    if input.sender.startswith('#'): return
    if input.owner: 
        phenny.proto.quit()
        __import__('os')._exit(0)
quit.commands = ['quit']
quit.priority = 'low'

def msg(phenny, input): 
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    a, b = input.group(2), input.group(3)
    if (not a) or (not b): return
    if input.admin: 
        phenny.msg(a, b)
msg.rule = (['msg'], r'(#?\S+) (.+)')
msg.priority = 'low'

def me(phenny, input): 
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    if input.admin: 
        msg = '\x01ACTION %s\x01' % input.group(3)
        phenny.msg(input.group(2), msg)
me.rule = (['me'], r'(#?\S+) (.*)')
me.priority = 'low'

if __name__ == '__main__': 
    print(__doc__.strip())
