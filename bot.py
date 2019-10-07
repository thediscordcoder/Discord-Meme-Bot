import os
import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
from make_requests import get_memes_urls
import asyncio
import json
import traceback

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

client = discord.Client()

with open("prefixes.json") as f:
    prefixes = json.load(f)
default_prefix = "!!"


with open("details.json") as f1:
    details_json = json.load(f1)
default_details = {"isEnabled": True,
                   "toStop": False}


def prefix(bot, message):
    id = message.guild.id
    return prefixes.get(id, default_prefix)


def details_isEnabled(bot, message):
    id = message.guild.id
    return details_json.get(id, default_details["isEnabled"])


def to_dump_details():
    with open("details.json", "w") as f1:
        json.dump(details_json, f1)


version = "v1.0.0"
bot = commands.Bot(command_prefix=prefix)


@bot.event
async def on_guild_join(g):
    success = False
    i = 0
    while not success:
        try:
            await g.channels[i].send(f"Hey there!! Thanks for inviting me to your server. To set a custom prefix, use `!!<prefix>`. For more help, use `!!help`.")
        except (discord.Forbidden, AttributeError):
            i += 1
        except IndexError:
            # if the server has no channels, doesn't let the bot talk, or all vc/categories
            pass
        else:
            success = True


# prefix command for custom prefix
@bot.command(name="prefix", help=": To change the prefix", pass_context=True)
@commands.has_permissions(administrator=True)
async def _prefix(ctx, new_prefix):

    prefixes[ctx.message.guild.id] = new_prefix
    with open("prefixes.json", "w") as f:
        json.dump(prefixes, f)


@bot.event
async def on_ready():
    print("Bot-O-Meme has started")


@bot.event
async def on_message(message):
    id = message.guild.id
    if id not in details_json:
        details_json[id] = {
            "isEnabled": True,
            "toStop": False
        }
        to_dump_details()

    await bot.process_commands(message)

# meme command
@bot.command(name="meme", help=": Shows a Meme")
async def meme(message):
    meme_list = get_memes_urls(1)
    for meme_set in meme_list[:1]:
        response_permalink = meme_set[0]
        response_title = meme_set[1]
        response_url = meme_set[2]
        colors = [0xff0000, 0x00ff00, 0x0000ff, 0x000000,
                  0xffffff, 0xffff00, 0x00ffff, 0xff00ff]
        random.shuffle(colors)
        emb = discord.Embed(title=response_title,
                            url=response_permalink, color=colors[0])
        emb.set_image(url=response_url)
        await message.send(embed=emb)


# start command
@bot.command(name="start", help=": Starts sending memes,space followed by latency in mins to send memes", enabled=default_details)
@commands.has_permissions(administrator=True)
async def start_memes_task(ctx, number_of_minutes: float):
    meme_list = get_memes_urls(10)

    if details_json[ctx.message.guild.id]["isEnabled"]:
        while True:
            for meme_set in meme_list:
                if details_json[ctx.message.guild.id]["toStop"]:
                    details_json[ctx.message.guild.id]["toStop"] = False
                    details_json[ctx.message.guild.id]["isEnabled"] = True
                    to_dump_details()
                    return

                if meme_set == meme_list[-1]:
                    meme_list = get_memes_urls(10)
                response_permalink = meme_set[0]
                response_title = meme_set[1]
                response_url = meme_set[2]
                colors = [0xff0000, 0x00ff00, 0x0000ff, 0x000000,
                          0xffffff, 0xffff00, 0x00ffff, 0xff00ff]
                random.shuffle(colors)
                emb = discord.Embed(title=response_title,
                                    url=response_permalink, color=colors[0])
                emb.set_image(url=response_url)
                await ctx.send(embed=emb)

                await asyncio.sleep(60 * number_of_minutes)
                details_json[ctx.message.guild.id]["isEnabled"] = False
                to_dump_details()

    else:
        details_json[ctx.message.guild.id]["isEnabled"] = False
        to_dump_details()
        return


# stop command
@bot.command(name="stop", help=": Stops sending memes", pass_context=True)
@commands.has_permissions(administrator=True)
async def stop_memes_task(ctx):

    if details_json[ctx.message.guild.id]["toStop"] == False and details_json[ctx.message.guild.id]["isEnabled"] == False:
        details_json[ctx.message.guild.id]["toStop"] = True
        to_dump_details()


@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
           # fails silently
        pass

    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'This command is on cooldown. Please wait {error.retry_after:.2f}s')

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You do not have the permissions to use this command.')

    # If any other error occurs, prints to console.
    else:
        print(''.join(traceback.format_exception(
            type(error), error, error.__traceback__)))

bot.run(TOKEN)
