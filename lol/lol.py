"""
https://developer.riotgames.com/terms-and-conditions.html
YOU EXPRESSLY ACKNOWLEDGE THAT YOU HAVE READ THESE API TERMS AND UNDERSTAND THE
RIGHTS, OBLIGATIONS, TERMS AND CONDITIONS SET FORTH HEREIN. BY CLICKING "I
ACCEPT" AND/OR ACCESSING AND CONTINUING TO USE THE RIOT DEVELOPER SITE, THE RIOT
GAMES API AND/OR ANY OTHER MATERIALS (EACH AS DEFINED BELOW), YOU (A) EXPRESSLY
CONSENT TO BE BOUND BY ITS TERMS AND CONDITIONS AND GRANT TO RIOT THE RIGHTS SET
FORTH HEREIN, AND (B) REPRESENT THAT YOU ARE OF LEGAL AGE TO FORM A BINDING
CONTRACT. IF YOU DISAGREE WITH ANY OF THESE API TERMS, RIOT DOES NOT GRANT YOU A
LICENSE TO ACCESS OR USE THE RIOT GAMES API OR ANY OTHER MATERIALS OWNED BY RIOT.
"""

import discord
import aiohttp
import json
import aiohttp
import operator
import collections
import os

from .utils.dataIO import fileIO, dataIO
from .utils import checks
try:
    from cassiopeia import riotapi
    isAvailable = True
except Exception as e:
    print(e)
    isAvailable = False

from __main__ import send_cmd_help
from discord.ext import commands


class League:
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xCC9835
        self.profile = "data/league/apikey.json"
        self.riceCog = dataIO.load_json(self.profile)
        self.api_error_lolchampgg = "Your API key for lolchamp.gg is invalid. Set it with `{}lolset lolchampgg [apikey]`"
        self.api_error_riot = "Your API key for riotgames is invalid. Set it with `{}lolset riot [apikey]`"
        try:
            riotapi_key = self.riceCog['riotapi']
            riotapi.set_api_key(riotapi_key)
            riotapi.set_region("eune")
            riotapi.get_lolsum_by_name("FwiedWice")
        except:
            print("Invalid API key for RIOTAPI.")
        try:
            lolchampgg_key = self.riceCog['lolchampgg']
        except:
            print("Invalid API key for lolchampGG.")


    @checks.is_owner()
    @commands.group(pass_context=True)
    async def lolset(self, ctx):
        """Set your api keys"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @lolset.command(pass_context=True)
    async def lolchampgg(self, ctx, apikey):
        """lolchamp.gg api key"""
        self.riceCog['lolchampgg'] = apikey
        dataIO.save_json(self.profile, self.riceCog)
        await self.bot.say("Done! You might want to delete the message containing your key.")

    @lolset.command(pass_context=True)
    async def about(self, ctx):
        await self.bot.say("Be sure to read this:\n"
                           "https://developer.riotgames.com"
                           "/terms-and-conditions.html")

    @lolset.command(pass_context=True)
    async def riot(self, ctx, apikey):
        """lolchamp.gg api key"""
        self.riceCog['riotapi'] = apikey
        dataIO.save_json(self.profile, self.riceCog)
        await self.bot.say("Done! You might want to delete the message containing your key.")

    @commands.command(pass_context = True)
    async def lolgame(self, ctx, region, *, lolsum):
        try:
            riot_apikey = self.riceCog['riotapi']
            riotapi.set_api_key(riot_apikey)
            riotapi.get_lolsum_by_name("FwiedWice")
        except:
            await self.bot.say(self.api_error_riot.format(ctx.prefix))
            return
        try:
            riotapi.set_region(region)
        except ValueError as e:
            print(e)
            await self.bot.say("Invalid region! Try again.")
            return
        except Exception as e:
            print(e)
            await self.bot.say("Check your console for logs.")
            return
        try:
            lolsum = riotapi.get_lolsum_by_name(lolsum)
        except Exception as e:
            print(e)
            await self.bot.say("Probably an invalid lolsum. Either wrong "
                               "lolsum name or region. Check your console.")
            return
        try:
            cur = lolsum.current_game()
            cur = cur.to_json()
            cur = json.loads(cur)
        except Exception as e:
            await self.bot.say("lolsum isn't in a game right now.")
            print(e)
            return

        #If lolchamps are banned
        banned_lolchamps_id = cur['bannedlolchamps']
        banned_lolchamps = []

        for champ_bans in banned_lolchamps_id:
            champ_name = riotapi.get_lolchamp_by_id(champ_bans['lolchampId'])
            banned_lolchamps.append(champ_name)

        participants = cur['participants']
        players = []
        chosen_one = lolsum.name
        #get players
        i = 0
        for participant in participants:
            i += 1
            player = {}
            lolsum = riotapi.get_lolsum_by_name(participant['lolsumName'])
            player['teamId'] = participant['teamId']
            player['lolchampId'] = participant['lolchampId']
            player['lolchampName'] = riotapi.get_lolchamp_by_id(participant['lolchampId'])
            player['lolsumId'] = participant['lolsumId']
            player['lolsumName'] = participant['lolsumName']
            players.append(player)
            try:#To get user tier and division and lp
                leagues = lolsum.leagues()
                name = lolsum.name
                tier = leagues[0].tier.name.title()
                tier_info = leagues[0].to_json()
                tier_info_dict = json.loads(tier_info)
                tier_users = tier_info_dict['entries']
                user_stats = [s for s in tier_users if s['playerOrTeamName'] == name]
                div = user_stats[0]['division']
                lp = user_stats[0]['leaguePoints']
                if div == "V":
                    div = "5"
                elif div == "IV":
                    div = "4"
                elif div == "III":
                    div = "3"
                elif div == "II":
                    div = "2"
                elif div == "I":
                    div = "1"
                losses = user_stats[0]['losses']
                wins = user_stats[0]['wins']
                total_games = wins + losses
                winrate = wins / total_games
                winrate = str(winrate)
                winrate = winrate[2:4]
                if len(winrate) == 1:
                    winrate += "0"
                player['winrate'] = winrate
                player['division'] = div
                player['tier'] = tier
                player['rank'] = "{}{}".format(tier[0], div)
            except Exception as e:
                print(e)
                pass

        #get what team you're on
        for player in players:
            if player['lolsumName'] == chosen_one:
                your_team_id = player['teamId']

        your_team = []
        enemy_team = []
        i = 0
        bans = ""
        for banned_lolchamp in banned_lolchamps:
            if i == 0:
                bans += "{}".format(banned_lolchamp)
            else:
                bans += ", {}".format(banned_lolchamp)
            i += 1

        #seperate teams
        for player in players:
            if player['teamId'] == your_team_id:
                your_team.append(player)
            else:
                enemy_team.append(player)

        msg = "```ruby\n"
        legend = "```{!s:<16}    {!s:<14}    {}\n```".format("lolsum:", "lolchamp:", "Winrate:")
        gsm = "```ruby\n"

        #List teammates and their champs
        for player in your_team:
            msg += "{!s:<16}    ".format(player['lolsumName'].replace("'", ""))
            msg += "{!s:<14}    ".format(player['lolchampName'].name.replace("'", ""))
            try:
                msg += "{!s:<2}% - {}\n".format(player['winrate'], player['rank'])
            except:
                msg += "   \n"

        for player in enemy_team:
            gsm += "{!s:<16}    ".format(player['lolsumName'].replace("'", ""))
            gsm += "{!s:<14}    ".format(player['lolchampName'].name.replace("'", ""))
            try:
                gsm += "{!s:<2}% - {}\n".format(player['winrate'], player['rank'])
            except:
                gsm += "   \n"

        region = region.upper()

        gsm += "```"
        msg += "```"

        #start embedding
        embed = discord.Embed(description="{}".format(cur['gameId']), color=self.color)
        embed.add_field(name="Region", value=region.upper())
        embed.add_field(name="Type", value=cur['gameMode'].lower().title())

        if bans != "":
            embed.add_field(name="Bans", value=bans, inline=False)
        else:
            embed.add_field(name="Bans", value="None", inline=False)

        embed.add_field(name="Legend", value=legend)

        embed.add_field(name="Your Team",value=msg, inline=False)

        embed.add_field(name="Enemy Team",value=gsm, inline=False)

        embed.set_author(name="{}'s current match".format(chosen_one))

        await self.bot.say(embed=embed)

    #@commands.command(pass_context = True) not releasable yet
    async def lastmatch(self, ctx, region, *, lolsum):
        try:
            riotapi.set_region(region)

        except ValueError as e:
            print(e)
            await self.bot.say("Invalid region! Try again.")
            return
        except Exception as e:
            print(e)
            await self.bot.say("Check your console for logs.")
            return
        try:
            lolsum = riotapi.get_lolsum_by_name(lolsum)
        except Exception as e:
            print(e)
            await self.bot.say("Probably an invalid lolsum. Either wrong "
                               "lolsum name or region. Check your console.")
            return
        player_stats = {}
        name = lolsum.name
        _id = lolsum.id
        region = region
        level = lolsum.level
        matches = lolsum.recent_games()
        last_match = matches[0].to_json()
        last_match = json.loads(last_match)
        match_type = last_match['subType'].title()
        deaths = last_match['stats']["numDeaths"]
        kills = last_match['stats']['lolchampsKilled']
        assists = last_match['stats']['assists']
        last_lolchamp_id = last_match['lolchampId']
        last_lolchamp_name = riotapi.get_lolchamp_by_id(last_lolchamp_id).name
        creeps = last_match['stats']["minionsKilled"]
        poop = True
        try:
            triple_kills = last_match['tripleKills']
            triple = True
        except:
            triple = False
        try:
            quadra_kills = last_match['quadraKills']
            quadra = True
        except:
            quadra = False
        try:
            penta_kills = last_match['pentaKills']
            penta = True
        except:
            penta = False
        msg =  "```ruby\n"
        msg += "Last Match of {}:\n\n".format(name)
        msg += "Match Type     -   {}\n".format(match_type)
        msg += "Region         -   {}\n".format(region.upper())
        msg += "lolchamp       -   {}\n".format(last_lolchamp_name)
        msg += "Score K/D/A    -   {}/{}/{}\n".format(kills, deaths, assists)
        msg += "Creep Score    -   {}".format(creeps)
        if triple:
            msg += "Triple Kills   -   {}".format(triple_kills)
        if quadra:
            msg += "Quadra Kills   -   {}".format(quadra_kills)
        if penta:
            msg += "Penta Kills    -   {}".format(penta_kills)

        msg += "```"
        await self.bot.say(msg)

    @commands.command(pass_context = True)
    async def lolsum(self, ctx, region, *, lolsum):
        try:
            riot_apikey = self.riceCog['riotapi']
            riotapi.set_api_key(riot_apikey)
            riotapi.get_lolsum_by_name("FwiedWice")
        except:
            await self.bot.say(self.api_error_riot.format(ctx.prefix))
            return
        try:
            riotapi.set_region(region)
        except ValueError as e:
            print(e)
            await self.bot.say("Invalid region! Try again.")
            return
        except Exception as e:
            print(e)
            await self.bot.say("Check your console for logs.")
            return
        try:
            lolsum = riotapi.get_lolsum_by_name(lolsum)
        except Exception as e:
            print(e)
            await self.bot.say("Probably an invalid lolsum. Either wrong "
                               "lolsum name or region. Check your console.")
            return

        #Get basic user info
        name = lolsum.name
        _id = lolsum.id
        region = region
        level = lolsum.level
        ma_pages = len(lolsum.mastery_pages())
        ru_pages = len(lolsum.rune_pages())
        if int(lolsum.level) == 30:#To get user tier and division and lp
            leagues = lolsum.leagues()
            tier = leagues[0].tier.name.title()
            tier_info = leagues[0].to_json()
            tier_info_dict = json.loads(tier_info)
            tier_users = tier_info_dict['entries']
            user_stats = [s for s in tier_users if s['playerOrTeamName'] == name]
            div = user_stats[0]['division']
            lp = user_stats[0]['leaguePoints']
            losses = user_stats[0]['losses']
            wins = user_stats[0]['wins']
            total_games = wins + losses
            winrate = wins / total_games
            winrate = str(winrate)
            winrate = winrate[2:4]
            if len(winrate) == 1:
                winrate += "0"
        try:
            top_champs = lolsum.top_lolchamp_masteries()
        except:
            pass

        #The message that is sent
        embed = discord.Embed(description = "{}".format(_id), color = self.color)
        embed.add_field(name="Region", value = region.upper())
        embed.set_thumbnail(url='http://vignette1.wikia.nocookie.net/leagueoflegends/images/1/12/League_of_Legends_Icon.png/revision/latest?cb=20150402234343')

        embed.set_author(name="{}".format(name))
        embed.add_field(name="Level", value = "{}".format(level))
        if int(lolsum.level) == 30:
            embed.add_field(name="Rank", value= "{} {}, {} LP".format(tier, div, lp))
            embed.add_field(name="Ranked W/L", value= "{}/{} - {}%".format(wins, losses, winrate))
        embed.add_field(name="Mastery Pages", value = str(ma_pages))
        embed.add_field(name="Rune Pages", value = str(ru_pages))
        try:
            title = "Top lolchamp Masteries:"
            i = 0
            msg = ""
            for champ in top_champs:
                if i == 0:
                    msg += "{}".format(champ)
                    i += 1
                else:
                    msg += " - {}".format(champ)
            embed.add_field(name=title, value=msg, inline=False)
        except:
            pass
        await self.bot.say(embed=embed)

    @commands.command(pass_context = True)
    async def lolchamp(self, ctx, *, lolchamp):
        try:
            riot_apikey = self.riceCog['riotapi']
            riotapi.set_api_key(riot_apikey)
            riotapi.get_lolsum_by_name("FwiedWice")
        except:
            await self.bot.say(self.api_error_riot.format(ctx.prefix))
            return
        lolchamp = lolchamp.title()
        try:
            champ = riotapi.get_lolchamp_by_name(lolchamp)
            champ.name
        except Exception as e:
            print(e)
            await self.bot.say("Probably an invalid lolchamp. Either wrong "
                               "name or error. Check your console.")
            return
        image_link = "http://ddragon.leagueoflegends.com/cdn/6.24.1/img/lolchamp/" + champ.image.link
        name = champ.name
        _id = champ.id
        champggname = champ.name.replace(" ", "").replace("'", "")
        champgg = 'http://api.lolchamp.gg'

        #get json from lolchamp.gg api
        try:
            lolchampgg_key = self.riceCog['lolchampgg']
            matchup_url = '{}/lolchamp/{}/matchup?api_key={}'.format(champgg, champggname, lolchampgg_key)
            async with aiohttp.get(matchup_url) as response:
                matchups = await response.json()
            matchup_list = matchups[0]["matchups"]
            #get matchups
            matchup_lolchamp = {}
        except:
            await self.bot.say(self.api_error_lolchampgg.format(ctx.prefix))
            return

        for matchup in matchup_list:
            enemy_champ = matchup['key']
            your_winrate = matchup['winRate']
            matchup_lolchamp[enemy_champ] = your_winrate

        sorted_matchup_lose = collections.OrderedDict(sorted(matchup_lolchamp.items(), key = lambda t: t[1]))
        sorted_matchup_win = collections.OrderedDict(sorted(matchup_lolchamp.items(), key = lambda t: t[1], reverse=True))
        general_winrate_url = '{}/lolchamp/{}/general?api_key={}'.format(champgg, champggname, lolchampgg_key)

        async with aiohttp.get(general_winrate_url) as response:
            general_winrate_list = await response.json()

        general_winrate_dic = general_winrate_list[0]
        general_winrate = general_winrate_dic['winPercent']['val']
        q = ""
        w = ""
        e = ""
        r = ""

        embed = discord.Embed(description="{}".format(_id), color = self.color)
        embed.set_thumbnail(url=image_link)
        embed.set_author(name="{}".format(champ.name), url=image_link)

        p = champ.passive.name
        roles = champ.tags
        abilities = [q, w, e ,r]
        spells = ["Q", "W", "E", "R"]
        i = 0
        while i <= 3:
            abilities[i] = champ.spells[i].name
            i += 1

        embed.add_field(name="Passive", value=p)
        embed.add_field(name="Winrate", value = "{}%".format(general_winrate))

        i = 0

        #Get skill order
        ability_url = '{}/lolchamp/{}/skills/mostPopular?api_key={}'.format(champgg, champggname, lolchampgg_key)
        async with aiohttp.get(ability_url) as response:
            skill_order_dic = await response.json()
        skill_order_info = skill_order_dic[0]
        skill_order = skill_order_info["order"]

        #Get item set
        items_url = '{}/lolchamp/{}/items/finished/mostPopular?api_key={}'.format(champgg, champggname, lolchampgg_key)
        async with aiohttp.get(items_url) as response:
            items_lists = await response.json()
        for items_dic in items_lists:
            if 'item' not in items_dic:
                continue
            elif items_dic['item'] != []:
                items_dic = items_dic
        items_list = items_dic["items"]
        items_set_role = items_dic['role']
        msg = ""
        cd = ""
        #Get abilities
        while i <= 3:
            ability = abilities[i]
            spell = spells[i]
            msg += "{}/{}".format(spell, ability)
            d = 0
            for cooldown in champ.spells[i].cooldowns:
                cooldown = str(cooldown).replace(".0", "")
                if d == 0:
                    cd += "{}".format(cooldown)
                    d += 1
                else:
                    cd += "/{}".format(cooldown)
            i += 1
            msg += "\n"
            cd += "\n"

        embed.add_field(name="Abilities", value=msg)
        embed.add_field(name="Cooldowns", value=cd)

        #say skill order
        msg = ""
        i = 0
        for skill in skill_order:
            if skill == None:
                skill = "R"
            if i == 0:
                msg += "{}".format(skill)
                i += 1
            else:
                msg += "/{}".format(skill)

        embed.add_field(name="Maxing order", value=msg)

        #get roles
        msg = ""
        i = 0
        for item in items_list:
            if i == 0:
                msg += "{}".format(riotapi.get_item(item).name.replace("'", "").replace('"', ""))
                i += 1
            else:
                msg += "\n{}".format(riotapi.get_item(item).name.replace("'", "").replace('"', ""))

        embed.add_field(name="Build path/{}".format(items_set_role), value=msg)

        try:
            msg = ""
            i = 0
            for role in roles:
                if i == 0:
                    msg += "{}".format(role)
                    i += 1
                else:
                    msg += " - {}".format(role)

            embed.add_field(name="Roles", value=msg)

        except:
            pass
        i = 0
        #Get counters
        msg = ""
        for champ in sorted_matchup_win:
            if i == 3:
                break
            elif i == 0:
                msg += "{} ({}%)".format(champ, sorted_matchup_win[champ])
            else:
                msg += "\n{} ({}%)".format(champ, sorted_matchup_win[champ])
            i += 1

        embed.add_field(name="Counters", value=msg)

        msg = ""
        i = 0
        for champ in sorted_matchup_lose:
            if i == 3:
                break
            elif i == 0:
                msg += "{} ({}%)".format(champ, sorted_matchup_win[champ])
            else:
                msg += "\n{} ({}%)".format(champ, sorted_matchup_win[champ])
            i += 1

        embed.add_field(name="Countered", value=msg)

        await self.bot.say(embed=embed)

def check_folder():
    if not os.path.exists("data/league"):
        print("Creating data/league folder")
        os.makedirs("data/league")

def check_file():
    data = {}
    f = "data/league/apikey.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/league/apikey.json")
        dataIO.save_json(f, data)



def setup(bot):
    check_folder()
    check_file()
    if isAvailable:
        bot.add_cog(League(bot))
    else:
        raise RuntimeError("You need to run `pip3 install cassiopeia`")
