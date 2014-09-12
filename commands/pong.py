from command import Command, register
import asyncio

class Pong(Command):
    @asyncio.coroutine
    def registered(self, server, user, proto, line):
        user.timeout = False


register['pong'] = Pong()
