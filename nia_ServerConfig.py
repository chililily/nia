import discord
from enum import Enum

class ServerConfig:
    def __init__(self,server_name):
        self.name = server_name

    @staticmethod
    def create(server,
               status_chnl=None,
               traffic_chnl=None,
               daily_chnl=None,
               roles=None,
               sa_roles=None,
               init=True):
        sc = ServerConfig(server.name)

        sc.status_chnl = discord.utils.get(server.channels, id=status_chnl, type=discord.ChannelType.text)
        sc.traffic_chnl = discord.utils.get(server.channels, id=traffic_chnl, type=discord.ChannelType.text)
        sc.daily_chnl = discord.utils.get(server.channels, id=daily_chnl, type=discord.ChannelType.text)
        if roles in (None,''):
            sc.roles = {}
        else:
            sc.roles = eval(roles)
        sc.sa_roles = {}
        if not sa_roles in (None,''):
            ids = eval(sa_roles)
            for _id in ids:
                role = discord.utils.get(server.roles, id=_id)
                sc.sa_roles[role.name] = role

        sc.is_dirty = init
        return sc

    """ Updates the current configuration.
    Parameters
    =================
    *_chnl:    <discord.Channel object> or <str> (channel id) 
    roles:     2-tuple (role id, message)
    """
    def update(self,
               status_chnl=None,
               traffic_chnl=None,
               daily_chnl=None,
               addrole=None,
               delrole=None,
               add_sar=None,
               del_sar=None):
        success = False
        if status_chnl != None:
            if type(status_chnl) == str:
                status_chnl = discord.utils.get(server.channels, id=status_chnl, type=discord.ChannelType.text)
            self.status_chnl = status_chnl
            success = True
        if traffic_chnl != None:
            if type(traffic_chnl) == str:
                traffic_chnl = discord.utils.get(server.channels, id=traffic_chnl, type=discord.ChannelType.text)
            self.traffic_chnl = traffic_chnl
            success = True
        if daily_chnl != None:
            if type(daily_chnl) == str:
                daily_chnl = discord.utils.get(server.channels, id=daily_chnl, type=discord.ChannelType.text)
            self.daily_chnl = daily_chnl
            success = True
        if addrole != None:
            self.roles[addrole[0]] = addrole[1]
            success = True
        if delrole != None:
            try:
                del self.roles[delrole]
                success = True
            except KeyError:
                pass
        if add_sar != None:
            if type(add_sar) == str:
                self.sa_roles[add_sar] = discord.utils.get(server.roles,name=add_sar)
                success = True
            elif type(add_sar) == discord.Role:
                self.sa_roles[add_sar.name] = add_sar
                success = True
        if del_sar != None:
            if type(del_sar) == str:
                try:
                    del self.sa_roles[del_sar]
                    success = True
                except KeyError:
                    pass
            elif type(del_sar) == discord.Role:
                try:
                    del self.sa_roles[del_sar.name]
                    success = True
                except KeyError:
                    pass
        if success:
            self.is_dirty = True
        return success

    def flatten(self):
        r = []
        for attr,value in self.__dict__.items():
            if value == None:
                r.append('')
            elif type(value) == bool:
                pass
            elif type(value) == discord.Channel:
                r.append(value.id)
            elif attr == 'roles':
                r.append(repr(value).replace("'","''"))
            elif attr == 'sa_roles':
                l = []
                for role in self.sa_roles.values():
                    l.append(role.id)
                r.append(repr(l).replace("'","''"))
        r.append(self.name)
        return r
        