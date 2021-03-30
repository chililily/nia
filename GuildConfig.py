import discord
from enum import Enum

class GuildConfig:
    def __init__(self,guild):
        self.id = guild.id
        self.name = guild.name

    @staticmethod
    def create(guild,
               status_chnl=None,
               traffic_chnl=None,
               dailies=None,
               announced_roles=None,
               sa_roles=None,
               init=True):
        gc = GuildConfig(guild)

        gc.status_chnl = discord.utils.get(guild.text_channels, id=status_chnl)
        gc.traffic_chnl = discord.utils.get(guild.text_channels, id=traffic_chnl)

        # Dailies
        # gc.dailies = []
        # chnls = eval(dailies)
        # for item in chnls:
        #     chnl1 = discord.utils.get(guild.text_channels, id=item[0])
        #     chnl2 = discord.utils.get(guild.text_channels, id=item[1])
        #     gc.dailies.append((chnl1,chnl2,item[2]))

        # Roles
        if announced_roles in (None,''):
            gc.announced_roles = {}
        else:
            gc.announced_roles = eval(announced_roles)

        # Self-assignable roles
        gc.sa_roles = {}
        if not sa_roles in (None,''):
            ids = eval(sa_roles)
            for _id in ids:
                role = discord.utils.get(guild.roles, id=_id)
                gc.sa_roles[role.name] = role

        gc.is_dirty = init
        return sc

    """ Updates the current configuration.
    Parameters
    =================
    *_chnl:    <discord.TextChannel object> or <int> (channel id) 
    roles:     2-tuple (role id, message)
    """
    def update(self,
               status_chnl=None,
               traffic_chnl=None,
               dailies=None,
               addrole=None,
               delrole=None,
               add_sar=None,
               del_sar=None):
        success = False
        if status_chnl != None:
            self.status_chnl = status_chnl[0]
            success = True

        if traffic_chnl != None:
            self.traffic_chnl = traffic_chnl[0]
            success = True

        if dailies != None:
            for chnl in dailies:
                self.dailies.append(chnl)
            success = True

        if addrole != None:
            self.announced_roles[addrole[0]] = addrole[1]
            success = True

        if delrole != None:
            try:
                del self.announced_roles[delrole]
                success = True
            except KeyError:
                pass
        if add_sar != None:
            if type(add_sar) == str:
                self.sa_roles[add_sar] = discord.utils.get(guild.roles,name=add_sar)
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
        r = [self.name]
        for attr,value in self.__dict__.items():
            if value == None:
                r.append('')
            elif type(value) == bool:
                pass
            elif type(value) == discord.TextChannel:
                r.append(value.id)
            elif attr == 'dailies':
                l = []
                for item in self.dailies:
                    l.append(item[0].id,item[1].id,item[2])
                # r.append(repr(l).replace("'","'"))
            elif attr == 'announced_roles':
                r.append(repr(value).replace("'","''"))
            elif attr == 'sa_roles':
                l = []
                for role in self.sa_roles.values():
                    l.append(role.id)
                r.append(repr(l).replace("'","''"))
        r.append(self.id)
        return r
        