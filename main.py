import os
import discord
from discord.ext import commands
from discord.ui import Button, View
import requests
import configparser
from time import sleep
import asyncio
import aiohttp
discordtoken=os.environ['discordtoken']
clientid=os.environ['clientid']
oauth=os.environ['oauth']
config=configparser.ConfigParser()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="twitch!", intents=intents)
USERS={}
notificationsent={}
@bot.command()
#Command to set which streamers nad games you recieve notifications for
async def setstreamer(ctx, username: str, * game: str):
  game=" ".join(game)
  #dictionary that stores multiple streamers and their associated game
  authorid=str(ctx.message.author.id)
  global USERS
  if username in USERS:
    USERS[username]=USERS[username]+","+game
  else:
    USERS[username]=game
  config.read('user.ini')
  if not config.has_section(authorid):
    prevexists=False
  else:
    #button only appears in the case that the discord user has run twitch!notifs before, meaning their preferences have been saved
    restoreButton=Button(label='Restore Previous Streamers')
    prevexists=True
    async def restoreButtonClicked(interaction):
      prevuserdict=dict(config.items(authorid))
      for key, value in prevuserdict.items():
        global USERS
        USERS[key]=value
      await interaction.response.send_message("Previous configurations restored successfully!")
    restoreButton.callback=restoreButtonClicked
  viewButton=Button(label='View Added Streamers', style=discord.ButtonStyle.green)
  async def viewButtonClicked(interaction):
    keylist=""
    viewiterations=0
    oneless=len(USERS)-1
    for key in USERS:
      viewiterations+=1
      if viewiterations==oneless:
        keylist+=key+', and '
      elif viewiterations==len(USERS):
        keylist+=key
      else:
        keylist+=key+", "
    if keylist=="":
      keylist="no one"
    await interaction.response.send_message(f"You have notifications on for {keylist}!")
  viewButton.callback=viewButtonClicked
  removeButton=Button(label='Remove Streamer', style=discord.ButtonStyle.red)
  async def removeButtonClicked(interaction):
    await interaction.response.send_message("Please send the username of the streamer you would like to remove.")
    message=await bot.wait_for('message')
    global USERS
    try:
      del USERS[message.content]
      await message.channel.send(f"{message.content} removed from notifications successfully!")
    except:
      await message.channel.send("Uh oh! That username is not inside your list of streamers! Try again, and make sure to be case accurate.")
  removeButton.callback=removeButtonClicked
  view=View()
  view.add_item(viewButton)
  view.add_item(removeButton)
  if prevexists==True:
    view.add_item(restoreButton)
  await ctx.reply(f"{username} added to notification list! Please run twitch!notifs to activate the notifications.", view=view)
@bot.command()
async def notifs(ctx):
  authorid=str(ctx.message.author.id)
  config[authorid]={}
  user = ctx.author
  for key, value in USERS.items():
    config[authorid][key]=value
  with open('user.ini', 'w')as userfile:
    config.write(userfile)
  await ctx.send('Notifications are on!')
  #dictionary that records whether or not a notification for a specific streamer has been sent
  global notificationsent
  notificationsent={}
  gamesent={}
  #loops online status check
  while True:
    #checks online status for each user in USERS
    for key, value in USERS.items():
      valuelist=value.split(",")
      async with aiohttp.ClientSession() as session:
        url= f"https://api.twitch.tv/helix/streams?user_login={key}"
        headers = {
          "Client-ID": clientid,
          "Authorization": oauth
        }
        #i represents each game the discord user has enabled for 1 streamer
        for i in valuelist: 
          #session request thing to not make asyncio spazz out     
          async with session.get(url, headers=headers) as response:
            data = await response.json()
            try:
            #success variable holds whether or not the streamer is online for one iteration of the while loop
              data['data'][0]['game_id']
              successful=True
            except:
              successful=False
              try:
                 notificationsent[key][i]
              except:
                continue
              else:
                del notificationsent[key][i]
            if successful==True:
            #converts game id to game name, then compares to user requested game name
              gameid=data['data'][0]['game_id']
              gameurl=f"https://api.twitch.tv/helix/games?id={gameid}"
              headers = {
                "Client-ID": clientid,
                "Authorization": oauth
              }
              async with session.get(gameurl, headers=headers) as gameresponse:
                gamedata=await gameresponse.json()
                gamename=gamedata['data'][0]['name']
                if gamename.lower()==i.lower():
                  try:
                    notificationsent[key]
                  except:
                    gamesent[i]='True'
                    notificationsent[key]=gamesent
                    await user.send(f"{key} is now live, streaming {gamedata['data'][0]['name']}! https://www.twitch.tv/{key}")
                  else:
                    if i not in notificationsent[key]:
                      gamesent[i]='True'
                      notificationsent[key]=gamesent
                      await user.send(f"{key} is now live, streaming {gamedata['data'][0]['name']}! https://www.twitch.tv/{key}")

    await asyncio.sleep(10)
bot.run(discordtoken)