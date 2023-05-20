import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import discord_self_embed
import requests
import json

import asyncio
import random

load_dotenv()

bot = commands.Bot(command_prefix='.', self_bot=True)

# CoinAPI (to get crypto prices lol)
def get_crypto_price(symbol: str):
    url = f"https://rest.coinapi.io/v1/exchangerate/{symbol}/USD"
    headers = {'X-CoinAPI-Key': '654FEA3C-712E-4E4C-B5DF-19FCAD8E7B56'}
    response = requests.get(url, headers=headers)
    return json.loads(response.text)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to selfbot 0.10!')


# Help command
@bot.command()
async def info(ctx):
    embed = discord_self_embed.Embed(f'Help', 
    description=f'.info - Shows this message\n.ping - Shows selfboy latency\n.dm @user - Sends the user a dm\n.crypto - Shows current prices for BTC and ETH\n.save_emojis - Saves emojis from a server (can be added into another server)\n.add_emojis - Adds emojis from save .txt file\n.purge (#) - purge certain ammount of messages (only used in DMs)\n.payme - Shows crypto addresss and way to pay me\n.whois - Whosis command',
    colour=f'#36393f')
    url = embed.generate_url(hide_url=True, shorten_url=False)
    await ctx.send(url)
    await ctx.message.delete()


# Ping command
@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong, {round(bot.latency * 1000)}ms')
    await ctx.message.delete()


# Crypto command
@bot.command()
async def crypto(ctx):
    btc_price = get_crypto_price("BTC")
    eth_price = get_crypto_price("ETH")
    embed = discord_self_embed.Embed(f'Crypto Prices', 
    description=f'BTC Price - ${btc_price["rate"]}\nETH Price - ${eth_price["rate"]}',
    colour='#36393f')
    url = embed.generate_url(hide_url=True, shorten_url=False)
    await ctx.send(url)
    await ctx.message.delete()


# Whois command
@bot.command()
async def whois(ctx, user: discord.User):
    embed = discord_self_embed.Embed(f'{user.name}s profile',
    description=f' 🧛‍♂️ Username : {user.name}#{user.discriminator}\n🔗 ID : {user.id}',
    colour='#36393f'
    )
    embed.set_image(url=user.avatar.url)
    url = embed.generate_url(hide_url=True, shorten_url=False)
    await ctx.send(url)
    await ctx.message.delete()


# Payme command
@bot.command()
async def payme(ctx):
  await ctx.send('\n<:btc:1014994181548146801> : `36a8fs4x8KPQhDc9unTuZiQ1ivi9oC766J`\n<:sl_fbethereum:1088952851587403869> : `0x500412969B9962e3682b33bF33801bc00a40061F`\n<:sl_cccashapp:1088304739734786148> : `$Jake9102`')
  await ctx.message.delete()


# Purge command 
@bot.command()
async def purge(ctx, limit: int):
    if isinstance(ctx.channel, discord.DMChannel):
        deleted_count = 0
        async for message in ctx.channel.history(limit=None):
            if message.author == bot.user:
                await message.delete()
                deleted_count += 1
                if deleted_count >= limit:
                    break
        await ctx.send(f'Deleted {deleted_count} messages lol...', delete_after=5)
    else:
        await ctx.send('This command can only be used in a DM channel!')


# DM command 
@bot.command()
async def dm(ctx, user: discord.User, *, message):
    await user.send(message)
    await ctx.send(f'Sent {user.name} a DM!')
    await ctx.message.delete()


# Save emojis command
@bot.command()
async def save_emojis(ctx):
    emojis = ctx.guild.emojis
    emoji_strings = [f"{emoji.name} : {emoji.url}" for emoji in emojis]
    emojis_text = '\n'.join(emoji_strings)
    server_name = ctx.guild.name.replace(' ', '_')
    filename = f"{server_name}_emojis.txt"
    with open(filename, 'w') as f:
        f.write(emojis_text)
    await ctx.send(f"Saved {len(emojis)} custom emojis to `{filename}`")
    await ctx.message.delete()


# Add emojis command
@bot.command()
async def add_emojis(ctx):
    filenames = [f for f in os.listdir() if f.endswith('.txt')]
    options = '\n'.join([f"{i+1}. {name}" for i, name in enumerate(filenames)])
    await ctx.send(f"Which file would you like to use? Here are your options:\n```{options}```")
    def check(message):
        return message.author == ctx.author and message.content.isdigit() and int(message.content) <= len(filenames)
    response = await bot.wait_for('message', check=check)
    selected_file = filenames[int(response.content) - 1]
    with open(selected_file, 'r') as f:
        emoji_strings = f.read().splitlines()
    messages = []
    for i, emoji_string in enumerate(emoji_strings):
        name, url = emoji_string.split(' : ')
        name = name.strip().replace(' ', '_')
        filename = os.path.basename(url)
        response = requests.get(url)
        with open(filename, "wb") as f:
            f.write(response.content)
        with open(filename, "rb") as f:
            emoji_bytes = f.read()
            try:
                emoji = await ctx.guild.create_custom_emoji(name=name, image=emoji_bytes)
                messages.append(f"Added emoji: {emoji}")
            except discord.HTTPException as e:
                if e.code == 429:
                    retry_after = e.retry_after
                    remaining_emojis = emoji_strings[i:]
                    messages.append(f"Server is being rate limited. Please wait {retry_after:.2f} seconds and try again.")
                    await asyncio.sleep(retry_after)
                    break
                else:
                    messages.append(f"Error adding emoji: {e}")
        os.remove(filename)
        await asyncio.sleep(2)
    if len(messages) > 0 and messages[-1].startswith("Server is being rate limited."):
        messages.pop()
        for emoji_string in remaining_emojis:
            name, url = emoji_string.split(' : ')
            name = name.strip().replace(' ', '_')
            filename = os.path.basename(url)
            response = requests.get(url)
            with open(filename, "wb") as f:
                f.write(response.content)
            with open(filename, "rb") as f:
                emoji_bytes = f.read()
                try:
                    emoji = await ctx.guild.create_custom_emoji(name=name, image=emoji_bytes)
                    messages.append(f"Added emoji: {emoji}")
                except discord.HTTPException as e:
                    messages.append(f"Error adding emoji: {e}")
            os.remove(filename)
            await asyncio.sleep(10)
    if messages:
        await ctx.send("\n".join(messages))
    else:
        await ctx.send('No custom emojis were added :(')
    await ctx.message.delete()




TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
