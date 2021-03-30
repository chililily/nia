"""
==============================================
TO-DO
------------
events
> phrases (no prefix)
> automatic roles

commands
> reformat help
> music player
> image search
> add command (from discord)
> quickdraw generator

other
> starboard
==============================================
"""

import random
import asyncio
import aiohttp
import discord
from discord import Game
from discord.ext.commands import Bot
import sqlite3
from GuildConfig import *
from MemberStats import *
from fuzzywuzzy import process      # fuzzy string matching
import datetime
# from Session import *
from constants import *
from dotenv import load_dotenv
import os

BOT_PREFIX = ("-")
DB_FILE = 'nia-data'

client = Bot(command_prefix=BOT_PREFIX,pm_help=None)
"""
==============================================
UTILITY FUNCTIONS
==============================================
(Internal use only.)
"""
def is_chnlMention(s):
    if len(s) < 3:
        return False
    if s[:2] == "<#" and s[-1] == ">" and s[2:-1].isdigit():
        return True
    return False

def chnl_id(mention: str):
    return mention.strip('<#>')

def is_daily(message: discord.Message):
    server = message.guild
    if server.name in server_configs:
        return message.channel == server_configs[server.name].daily_chnl and message.content.startswith("```ini")

def make_global(url):
    return url.replace("webp","png")

""" Placeholder for not-yet-completed features. """
async def reject(channel):
    await channel.send(random.choice(REJECTS))


"""
==============================================
BOT COMMANDS
==============================================
"""

@client.command(name='ping')
async def test(context):
    user = context.author
    await context.send(embed=discord.Embed(description=":ping_pong: Pong!"))

@client.command(name='abt',
                brief="Adds/remove autoban trigger (usernames)")
async def autoban_trigger(context,arg):
    reject(context)


"""
==============================================
BOT CONFIGURATION COMMANDS
==============================================
.edit avatar:       Set bot's avatar.
.edit pfp:          Alias for .edit avatar.
.edit nick:         Set bot's nickname.
"""
@client.command(name='edit',
                description="Set of bot configuration commands.")
async def edit_bot(context, *args):
    if len(args) != 0:
        if args[0] == 'avatar' or args[0] == 'pfp':
            await reject(context.channel)
        elif args[0] == 'nick':
            # [+] add case for resetting nick (no input)
            if len(args) > 1:
                new_nick = ' '.join(args[1:])
                if len(new_nick) <= 32:
                    await context.me.edit(nick=' '.join(args[1:]))
                else:
                    await context.send(embed=discord.Embed(description="Nicknames must be 32 characters or fewer in length.", colour=ERROR_CLR))



"""
==============================================
SERVER CONFIGURATION COMMANDS
==============================================
.sconfig status:        Sets the status channel (role update messages).
.sconfig traffic:       Sets the traffic channel (join/leave messages).
.sconfig daily:         Sets the daily channel (pinning).
.sconfig addrole:       Add a role to be announced, with message surrounded by backticks. Type <user> to have the user be mentioned.
.sconfig delrole:       Deletes a role from announcements.
"""
@client.command(name='sconfig',
                description="Set of server configuration commands.",
                aliases=['sc'],
                pass_context=True)
async def set_serverConfig(context, *args):
    server = context.guild
    # Initialize entry if not existing
    if not server.name in server_configs:
        server_configs[server.name] = GuildConfig.create(server)
    config = server_configs[server.name]
        
    # Process arguments.    
    if len(args) < 2:
        return
    if args[0] == 'status' or args[0] == 'traffic' or args[0] == 'daily':
        chnl_mentions = context.message.channel_mentions
        if len(chnl_mentions) > 0:
            if args[0] == 'status' and len(chnl_mentions) == 1:
                success = config.update(status_chnl=chnl)
                if success:
                    await context.send(embed=discord.Embed(description="Status channel set to "+chnl_mention+'. All update notices for indicated roles will be sent there.', colour=server.me.colour))
            elif args[0] == 'traffic' and len(chnl_mentions) == 1:
                success = config.update(traffic_chnl=chnl)
                if success:
                    await context.send(embed=discord.Embed(description="Traffic channel set to "+chnl_mention+'. All join/leave notices will be sent there.', colour=server.me.colour))
            elif args[0] == 'daily':
                # success = config.update(dailies=chnl_mentions)
                # if success:
                #     await context.send(embed=discord.Embed(description="Daily channel set to "+chnl_mention+'.', colour=server.me.colour))
                reject(context)
    elif args[0] == 'addrole':
        parts = ' '.join(args[1:]).split('`')
        rolename = parts[0].strip(' ')
        role = discord.utils.get(server.roles, name=rolename)
        if role != None:
            success = config.update(addrole=(role.id, parts[1]))
            if success:
                await context.send(embed=discord.Embed(description="Added `"+rolename+"` to announced roles.", colour=server.me.colour))
    elif args[0] in ['delrole', 'rmrole']:
        rolename = ' '.join(args[1:])
        role = discord.utils.get(server.roles, name=rolename)
        if role != None:
            success = config.update(delrole=role.id)
            if success:
                await context.send(embed=discord.Embed(description="Deleted `"+rolename+"` from announced roles.", colour=server.me.colour))


""" Retrieve server configuration info, set by .setconfig """
@client.command(name='getconfig',
                aliases=['gc'],
                pass_context=True)
async def get_serverConfig(context, arg):
    server = context.guild

    if server.name in server_configs:
        response = None
        if arg == 'status':
            response = server_configs[server.name].status_chnl.mention
        elif arg == 'traffic':
            response = server_configs[server.name].traffic_chnl.mention
        elif arg == 'daily':
            # response = ""
            # for chnl in server_configs[server.name].dailies:
            #     response.append(chnl.mention)
            reject(context)
        elif arg == 'roles':
            response = ""
            for _id in server_configs[server.name].announced_roles:
                role = discord.utils.get(server.announced_roles, id=_id)
                response += '`'+role.name+'`'+' | `'+server_configs[server.name].announced_roles[_id]+'`\n'
            response.strip('\n')

        if response in (None,""):
            await reject(context)
        else:
            await context.send(response)


@client.command(name='dailypins',pass_context=True)
async def daily_pins(context, num=PIN_LIMIT):
    # server = context.guild
    # for chnl_id in server_configs[server.name].dailies:
    #     pins = server.get_channel(chnl_id)
    #     show = len(pins)
    #     if num < show:
    #         show = num
    #     for i in range(show):
    #         await context.send(embed=discord.Embed(title=' '.join(['#',str(i),str(pins[i].author),str(pins[i].created_at)]), description=pins[i].content))
    reject(context)


"""
==============================================
SELF-ASSIGNABLE ROLES (SARs)
==============================================
.asar       Make a role self-assignable
.rsar       Make a role not self-assignable
.lsar       List all SARs
.iam        Add a SAR to self
.iamnot     Remove a SAR from self
"""
@client.command(name='asar',
                brief="Makes an existing role self-assignable.",
                pass_context=True)
async def add_sar(context, *args):
    author = context.author
    
    if not author.server_permissions.manage_roles:
        await context.send(embed=discord.Embed(description=":no_entry: You need the **Manage roles** permission to edit self-assignable roles.", colour=ERROR_CLR))
        return

    server = context.guild
    if not server.name in server_configs:
        server_configs[server.name] = GuildConfig.create(server)
    config = server_configs[server.name]

    rolename = ' '.join(args)
    role = discord.utils.get(server.announced_roles, name=rolename)
    success = config.update(add_sar=role)
    if success:
        await context.send(embed=discord.Embed(description="Role `"+rolename+"` is now self-assignable.", colour=server.me.colour))

@client.command(name='rsar',
                brief="Removes role from list of self-assignable roles.",
                aliases=['dsar'],
                pass_context=True)
async def del_sar(context, *args):
    author = context.author
    
    if not author.server_permissions.manage_roles:
        await context.send(embed=discord.Embed(description=":no_entry: You need the **Manage roles** permission to edit self-assignable roles.", colour=ERROR_CLR))
        return

    server = context.guild
    if server.name in server_configs:
        config = server_configs[server.name]

        rolename = ' '.join(args)
        success = config.update(del_sar=rolename)
        if success:
            await context.send(embed=discord.Embed(description="Role `"+rolename+"` is no longer self-assignable.", colour=server.me.colour))

@client.command(name='lsar',
                brief="Lists self-assignable roles.",
                pass_context=True)
async def list_sar(context):
    ls = ""
    server = context.guild
    if server.name in server_configs:
        config = server_configs[server.name]
        names = []
        for rolename in config.sa_roles:
            names.append(rolename)
        names.sort()
        for rolename in names:
            ls += rolename+'\n'
        ls.strip('\n')
    await context.send(embed=discord.Embed(title="List of self-assignable roles:",description=ls, colour=server.me.colour))

@client.command(name='iam',
                brief="Self-assigns a role.",
                pass_context=True)
async def iam(context, *args):
    server = context.guild
    member = context.author
    
    if not server.name in server_configs:
        server_configs[server.name] = GuildConfig.create(server)
    config = server_configs[server.name]
    if member.nick != None:
        name = member.nick
    else:
        name = str(member)

    rolename = ' '.join(args)
    result = process.extractOne(rolename, list(config.sa_roles.keys()))
    print(rolename, result)
    if result != None and result[1] >= 90:
        role = config.sa_roles[result[0]]
        if role in member.roles:
            await context.send(embed=discord.Embed(description=name+", you already have the role **"+result[0]+"**.", colour=ERROR_CLR))
        else:
            await client.add_roles(member,role)
            await context.send(embed=discord.Embed(description=name+", you now have the role **"+result[0]+"**.", colour=server.me.colour))

@client.command(name='iamnot',
                brief="Removes a self-assignable role.",
                pass_context=True)
async def iamnot(context, *args):
    server = context.guild
    member = context.author
    if not server.name in server_configs:
        server_configs[server.name] = GuildConfig.create(server)
    config = server_configs[server.name]
    if member.nick != None:
        name = member.nick
    else:
        name = str(member)

    rolename = ' '.join(args)
    result = process.extractOne(rolename, list(config.sa_roles.keys()))
    print(rolename, result)
    if result != None and result[1] >= 90:
        role = config.sa_roles[result[0]]
        if role in member.roles:
            await client.remove_roles(member,role)
            await context.send(embed=discord.Embed(description=name+", you no longer have the role **"+result[0]+"**.", colour=server.me.colour))


"""
==============================================
MISC COMMANDS
==============================================
"""
@client.command(name='8ball',
                description="Answers a yes/no question.",
                brief="Answers from the beyond.",
                aliases=['eight_ball', 'eightball', '8-ball'],
                pass_context=True)
async def eight_ball(context):
    await context.send(random.choice(EIGHT_BALL) + ", " + context.author.mention)


""" Shows profile for a user (if no mention, shows profile for the requesting user). """
@client.command(name='userinfo',
                description="Displays the profile for a user.",
                aliases=['whois','profile','activity'],
                pass_context=True)
async def show_profile(context, arg=None):
    server = context.guild
    mentions = context.message.mentions
    if arg == None:
        member = context.author
    elif len(mentions) > 0:
        member = mentions[0]
    elif arg.isdigit():
        member = discord.utils.get(server.members, id=arg)
    if member.nick != None:
        name = member.nick+' ('+str(member)+')'
    else:
        name = str(member)

    c_id = str(member.id)+'.'+str(context.guild.id)
    if not c_id in member_stats:
        member_stats[c_id] = MemberStats.create(member=member, server=server)
    ms = member_stats[c_id]
    stats = ms.getStats()
    chnls = []
    for chnl_stat in stats[3]:
        chnls.append(discord.utils.get(server.channels, id=chnl_stat[1]))
    top_chnls = ''
    for chnl in chnls:
        top_chnls += chnl.mention+', '
    top_chnls = top_chnls.strip(', ')


    embed = discord.Embed(title=name,
                          colour=member.colour)
    embed.set_footer(text="ID: "+str(member.id)+' \u2022 Activity stats since '+server.created_at.strftime("%b %d, %Y"))
    embed.set_thumbnail(url=make_global(str(member.avatar_url)))
    embed.add_field(name="Joined",
                    value=member.joined_at.strftime("%a, %b %d %Y at %H:%M"),
                    inline=True)
    embed.add_field(name="Total messages",
                    value=str(stats[0]),
                    inline=True)
    embed.add_field(name="Messages (last 7 days)",
                    value=str(stats[1]),
                    inline=True)
    embed.add_field(name="Messages (last 24 hours)",
                    value=str(stats[2]),
                    inline=True)
    embed.add_field(name="Top channels",
                    value=top_chnls,
                    inline=True)
    await context.send(embed=embed)


@client.command(name='log',
                brief="Process messages from <channel>",
                pass_context=True)
async def log_messages(context):
    for _id in member_stats:
        if member_stats[_id].server_id == str(context.guild.id):
            member_stats[_id].reset()

    for chnl in context.guild.channels:
        if isinstance(chnl,discord.TextChannel):
            perms = chnl.permissions_for(context.me)
            if not perms.read_message_history:
                print("Skipped #"+chnl.name+'.')
                continue
            i = 0
            async for msg in chnl.history(limit=None,oldest_first=True):
                c_id = str(msg.author.id)+'.'+str(msg.guild.id)
                if not c_id in member_stats:
                    member_stats[c_id] = MemberStats.create(member=msg.author, server=msg.guild)
                ms = member_stats[c_id]
                ms.add(msg)

                last = msg.created_at
                i += 1
            print("Logged "+str(i)+" message(s) from #"+chnl.name+'.')
    print("Done!")


@client.command(name='play',
                brief="Adds <YT link / search term> to playlist.",
                pass_context=True)
async def play(context, arg):
    reject(context)


"""
==============================================
UNIT CONVERSIONS
==============================================
Currently only supports F/C temperature conversions.

"""
@client.command(name='convert',
                pass_context=True)
async def convert(context, u_from, u_to, quantity):
    try:
        q = float(quantity)
    except ValueError:
        await context.send(embed=discord.Embed(description="I need a number to convert!",colour=ERROR_CLR))

    # Temperature
    if u_from.lower() == 'c' and u_to.lower() == 'f':
        await context.send(embed=discord.Embed(description=quantity+"\u00b0C is equal to "+str(round(float(quantity)*(9/5)+32, 1))+"\u00b0F.",colour=SUCCESS_CLR))
    elif u_from.lower() == 'f' and u_to.lower() == 'c':
        await context.send(embed=discord.Embed(description=quantity+"\u00b0F is equal to "+str(round((float(quantity)-32)*(5/9), 1))+"\u00b0C.",colour=SUCCESS_CLR))

    # Weight
    # elif u_from.lower() == 'kg' and u_to.lower() == 'lbs':
    else:
        await context.send(embed=discord.Embed(description="Sorry, I can only do Celsius/Fahrenheit conversions right now :(",colour=ERROR_CLR))

"""
==============================================
EVENTS
==============================================
"""

@client.event
async def on_ready():
    await client.change_presence(activity=Game(name="with humans"))
    print("Logged in as " + client.user.name)

@client.event
async def on_member_join(member):
    for word in AUTOBAN_TRIGGERS:
        if word in member.name:
            await client.ban(member)
            return

""" Announces preset message when user obtains an announceable role. """
@client.event
async def on_member_update(before,after):
    server = before.guild
    if server.name in server_configs:
        config = server_configs[server.name]
        if config.status_chnl != None:
            for role_id in config.roles:
                role = discord.utils.get(server.roles, id=role_id)
                if (not role in before.roles) and (role in after.roles):
                    message = config.roles[role_id]
                    message = message.replace("<user>", after.mention)
                    await client.send_message(config.status_chnl, message)


""" Notifies when a member leaves the server. The message is sent to the traffic channel, if it has been specified. """
@client.event
async def on_member_remove(member):
    server = member.guild
    if server.name in server_configs:
        config = server_configs[server.name]
        if config.traffic_chnl != None:
            await client.send_message(config.traffic_chnl, embed=discord.Embed(description='**'+str(member)+"** has left the server.", colour=LEAVE_COLOUR))

""" Various handling of messages. """
@client.event
async def on_message(message):
    server = message.guild
    c_id = str(message.author.id)+'.'+str(server.id)
    if not c_id in member_stats:
        member_stats[c_id] = MemberStats.create(member=message.author, server=server)
    ms = member_stats[c_id]
    ms.add(message)

    await client.process_commands(message)

    # daily stuff
    # if server.name in server_configs:
    #     config = server_configs[server.name]
    #     if message.type == discord.MessageType.pins_add and message.channel == config.daily_chnl:
    #         await client.delete_message(message)
    #     elif is_daily(message):
    #         pins = await client.pins_from(message.channel)
    #         if len(pins) == PIN_LIMIT:
    #             await client.unpin_message(pins[-1])
    #         await client.pin_message(message)

"""
==============================================
CLIENT STUFF
==============================================
"""


async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed():
        print("Current servers:")
        for server in client.guilds:
            print('- '+server.name)
        await asyncio.sleep(1800)

async def load_db():
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS guild_configs(gid INT PRIMARY KEY, name TEXT, status_chnl INT, traffic_chnl INT, announced_roles TEXT);")
    c.execute("CREATE TABLE IF NOT EXISTS member_stats(c_id TEXT PRIMARY KEY, server_id TEXT, total INTEGER, chnl_stats TEXT, last_7d TEXT, last_24h TEXT);")

    # Get a list of servers bot is currently a member of...
    server_names,server_ids = [],[]
    for server in client.guilds:
        server_names.append(server.name)
        server_ids.append(str(server.id))

    # ...and fetch the configurations for those servers
    c.execute("SELECT * FROM guild_configs WHERE name IN ({})".format(repr(server_names).strip('[]')))
    rows = c.fetchall()
    for row in rows:
        server = discord.utils.get(client.guilds, name=row[0])
        server_configs[row[0]] = GuildConfig.create(server, *row[1:], False)

    # Fetch user statistics for users sharing a server with this bot
    c.execute("SELECT * FROM member_stats WHERE server_id IN ({})".format(repr(server_ids).strip('[]')))
    rows = c.fetchall()
    for row in rows:
        member_stats[row[0]] = MemberStats.create(c_id=row[0], total=row[2], chnl_stats=row[3].replace("''","'"), last_7d=row[4], last_24h=row[5], init=False)

    return db

async def manage_db():
    await client.wait_until_ready()

    db = await load_db()
    c = db.cursor()
    while not client.is_closed():
        for server in server_configs:
            config = server_configs[server]
            if config.is_dirty:
                data = config.flatten()
                c.execute("SELECT * FROM guild_configs WHERE name='{}';".format(config.name))
                row = c.fetchone()
                if row != None:
                    c.execute("UPDATE guild_configs SET name='{}', status_chnl={}, traffic_chnl={}, daily_chnl={}, announced_roles='{}', sa_roles='{}' WHERE gid={};".format(*data))
                else:
                    c.execute("INSERT INTO guild_configs (gid, status_chnl, traffic_chnl, daily_chnl, roles, sa_roles, name) VALUES (?,?,?,?,?,?);", data)
        db.commit()
        for server in server_configs:
            server_configs[server].is_dirty = False

        for c_id in member_stats:
            ms = member_stats[c_id]
            if ms.is_dirty:
                data = ms.flatten()
                c.execute("SELECT * FROM member_stats WHERE c_id='{}';".format(ms.get_cID()))
                row = c.fetchone()
                if row != None:
                    c.execute("UPDATE member_stats SET server_id='{}', total={}, chnl_stats='{}', last_7d='{}', last_24h='{}' WHERE c_id='{}';".format(*data))
                else:
                    c.execute("INSERT INTO member_stats (server_id, total, chnl_stats, last_7d, last_24h, c_id) VALUES (?,?,?,?,?,?);", data)
        db.commit()
        for c_id in member_stats:
            member_stats[c_id].is_dirty = False

        print(datetime.datetime.now().strftime("%H:%M %m-%d-%y")+": Autosaved database.")
    await asyncio.sleep(60)


server_configs = {}
member_stats = {}
client.loop.create_task(list_servers())
client.loop.create_task(manage_db())
load_dotenv('.env')
client.run(os.getenv('TOKEN'))