import os
import discord
from discord.ext import commands
from discord.ui import Button, View
import requests
import configparser
from time import sleep
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
async def setstreamer(ctx, username: str, game: str):
  #dictionary that stores multiple streamers and their associated game
  discorduser=ctx.message.author.id
  print(discorduser)
  global USERS
  USERS[username]=game
  try:
     config[ctx.message.author.id]
  except:
    prevexists=False
  else:
    restoreButton=Button(label='Restore Previous Streamers')
    async def restoreButtonClicked(interaction):
      prevuserdict=dict(config.items(ctx.message.author.id))
      for key, value in prevuserdict:
        print(key+" "+value)
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
  await ctx.reply(f"{username} added to notification list! Once you're done adding your streamers, please run twitch!notifs to activate the notifications.", view=view)
@bot.command()
async def notifs(ctx):
  authorid=str(ctx.message.author.id)
  config[authorid]={}
  for key, value in USERS.items():
    config[authorid][key]=value
  with open('user.ini', 'w')as userfile:
    config.write(userfile)
  await ctx.send('Notifications are on!')
  #dictionary that records whether or not a notification for a specific streamer has been sent
  global notificationsent
  notificationsent={}
  #loops online status check
  while True:
    #checks online status for each user in USERS
    for key, value in USERS.items():
        
      url= f"https://api.twitch.tv/helix/streams?user_login={key}"
      headers = {
        "Client-ID": clientid,
        "Authorization": oauth
      }
      response = requests.get(url, headers=headers)
      data = response.json()
      try:
        #success variable holds whether or not the streamer is online for one iteration of the while loop
        data['data'][0]['game_id']
        successful=True
      except:
        successful=False
        try:
           notificationsent[key]
        except:
          continue
        else:
          del notificationsent[key]
      if successful==True:
        #converts game id to game name, then compares to user requested game name
        gameid=data['data'][0]['game_id']
        gameurl=f"https://api.twitch.tv/helix/games?id={gameid}"
        headers = {
          "Client-ID": clientid,
          "Authorization": oauth
        }
        gameresponse=requests.get(gameurl, headers=headers)
        gamedata=gameresponse.json()
        gamename=gamedata['data'][0]['name']
        gamename=gamename.replace(" ","_")
        if gamename.lower()==value.lower():
          if key not in notificationsent:
            user = ctx.author
            notificationsent[key]="True"
            await user.send(f"{key} is now live, streaming {gamedata['data'][0]['name']}! https://www.twitch.tv/{key}")
          
    #time.sleep(5) test if this works
bot.run(discordtoken)