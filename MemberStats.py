import discord
import datetime
from enum import Enum
from operator import itemgetter
from heapq import nlargest

WEEK = datetime.timedelta(weeks=1)
DAY = datetime.timedelta(days=1)

class MemberStats:
    def __init__(self,_id,server_id):
        self.id = _id
        self.server_id = server_id

    @staticmethod
    def create(c_id=None,
               member=None,
               server=None,
               total=0,
               chnl_stats=None,
               last_7d=None,
               last_24h=None,
               init=True):
        if c_id != None:
            parts = c_id.split('.')
            ms = MemberStats(*parts)
        elif server == None:
            ms = MemberStats(str(member.id), str(member.server.id))
        else:
            ms = MemberStats(str(member.id), str(server.id))

        ms.total = total
        if chnl_stats in (None,''):
        	ms.chnl_stats = {}
        else:
        	ms.chnl_stats = eval(chnl_stats)
        if last_7d in (None,''):
        	ms.last_7d = []
        else:
        	ms.last_7d = eval(last_7d)
        if last_24h in (None,''):
        	ms.last_24h = []
        else:
	        ms.last_24h = eval(last_24h)

        ms.is_dirty = init
        return ms

    """ Adds new data to stats. """
    def add(self, msg:discord.Message):
        self.total += 1
        if msg.channel.id in self.chnl_stats:
        	self.chnl_stats[msg.channel.id] += 1
        else:
        	self.chnl_stats[msg.channel.id] = 1
        if datetime.datetime.utcnow() - msg.created_at <= WEEK:
        	self.last_7d.append(msg.created_at)
        if datetime.datetime.utcnow() - msg.created_at <= DAY:
        	self.last_24h.append(msg.created_at)
        self.is_dirty = True

    def update(self):
        start = 0
        self.last_7d.sort()
        self.last_24h.sort()

        for i in range(len(self.last_7d)):
            if datetime.datetime.utcnow() - self.last_7d[i] <= WEEK:
                start = i
                break
        self.last_7d = self.last_7d[start:]
        if start != 0:
            self.is_dirty = True
        for i in range(len(self.last_24h)):
            if datetime.datetime.utcnow() - self.last_24h[i] <= DAY:
                start = i 
                break
        self.last_24h = self.last_24h[start:]
        if start != 0:
            self.is_dirty = True

    def getStats(self):
        if self.chnl_stats != {}:
            top_stats = nlargest(3, ((value,key) for key,value in self.chnl_stats.items()))
        else:
            top_stats = None
        self.update()
        return (self.total, len(self.last_7d), len(self.last_24h), top_stats)

    def get_cID(self):
        return self.id+'.'+self.server_id

    def reset(self):
        self.total = 0
        self.chnl_stats = {}
        self.last_7d = []
        self.last_24h = []

    def flatten(self):
        r = []
        for attr,value in self.__dict__.items():
            if value in (None,[],{}):
                r.append('')
            elif attr == 'server_id':
                r.append(self.server_id)
            elif type(value) == int:
                r.append(value)
            elif type(value) == bool or type(value) == str:
                pass
            else:
                r.append(repr(value).replace("'","''"))
        r.append(self.get_cID())
        return r
