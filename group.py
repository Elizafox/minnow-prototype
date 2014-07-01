from collections import defaultdict
from user import DCPUser
from parser import MAXFRAME
from time import time

class DCPGroup:
    """ Like an IRC channel """
    def __init__(self, proto, name, topic=None, acl=None, ts=None):
        self.proto = proto
        self.name = name
        self.topic = topic
        self.acl = acl
        self.users = set()
        self.ts = None

        if self.acl is None:
            self.acl = defaultdict(list) 

        if self.ts is None:
            self.ts = round(time.time())

        if not self.name.startswith('#'):
            self.name = '#' + self.name

    def member_add(self, user, reason=None):
        if user in self.users:
            raise Exception('Duplicate addition')

        self.users.add(user)
        user.groups.add(self)

        kval = {}
        if reason:
            kval['reason'] = [reason]

        self.send(user.handle, self, 'group-enter', kval)

        # Burst the channel info
        kval = {
            'time' : [str(self.ts)],
            'topic' : [self.topic if self.topic else ''],
        }
        user.send(self, user.handle, 'group-info', kval)

        kval = {
            'users' : []
        }

        d_tlen = tlen = 500 # Probably too much... but good enough for now.
        for user2 in self.users:
            tlen += len(user2.name) + 1
            if tlen >= MAXFRAME:
                # Overflow... send what we have and continue
                user.send(self, user.handle, 'group-names', kval)
                tlen = d_tlen + len(user2.name) + 1

            kval['users'].append(user2.name)

        # Burst what's left
        if len(kval['users']) > 0:
            user.send(self, user.handle, 'group-names', kval)

        # Burst ACL's
        kval = {
            'acl' : [],
        }
        user.send(self, user.handle, 'acl-list', None)

    def member_del(self, user, reason=None, permanent=False):
        if user not in self.users:
            raise Exception('Duplicate removal')

        self.users.remove(user)
        user.groups.remove(self)

        kval = defaultdict(list)
        if not reason:
            reason = ['']
        
        kval['reason'].append(reason)

        if permanent:
            kval['quit'] = '*'

        self.send(user.handle, self.name, 'group-exit', kval)

    def message(self, source, message):
        # TODO various ACL checks
        if isinstance(source, DCPUser) and source not in self.users:
            self.server.error(source, 'message', 'You aren\'t in that group',
                              False)
            return

        kval = defaultdict(list)
        kval['body'] = message

        self.send(self.name, user.handle, 'message', kval, [source])

    def send(self, source, target, command, kval=None, filter=[]):
        for user in self.users:
            if user in filter:
                continue

            user.send(source, target, self.name, command, kval)

