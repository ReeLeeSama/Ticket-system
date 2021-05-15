import discord
import asyncio
import aiofiles


from discord.ext import commands

intents = discord.Intents.all()
client = commands.Bot(command_prefix=commands.when_mentioned_or('!'),intents=intents)
client.ticket_configs = {}

@client.command()
async def ping(ctx):
    embed=discord.Embed(title="Bot Ping",description=f"My ping is {round(client.latency * 1000)}ms ",color=discord.Colour.gold())
    await ctx.reply(embed=embed)

@client.event
async def on_raw_reaction_add(payload): #When a reaction is added
    if payload.member.id != client.user.id and str(payload.emoji) == u"\U0001F3AB": #Checks if the reaction is not made by a bot an emoji is "🎫"
        msg_id, channel_id, category_id = client.ticket_configs[payload.guild_id] 

        if payload.message_id == msg_id: #checks if the reaction message is equal to the message id in ticket_configs.txt
            guild = client.get_guild(payload.guild_id)

            for category in guild.categories:
                if category.id == category_id:
                    break

            channel = guild.get_channel(channel_id) #gets the channel id

            ticket_channel = await category.create_text_channel(f"ticket-{payload.member.display_name}", topic=f"Ticket for {payload.member.display_name}.", permission_synced=True) #Creates a ticket as "ticket_channel"
            f = open(f"tickets/{ticket_channel.id}.txt", "w") #Opens a folder called "tickets" and inside it creates a file with the channel id. Usefull for transcripts
            f.close() #closes the file
            await ticket_channel.set_permissions(payload.member, read_messages=True, send_messages=True) # Adds the member to the ticket
            mention_member = f"{payload.member.mention}" 
            message = await channel.fetch_message(msg_id)
            await message.remove_reaction(payload.emoji, payload.member) #Removes the reaction for the message where you react to make a ticket
            creation_embed=discord.Embed(title="Ticket Created",description="Thank you for creating a ticket and make sure that the ticket follows our ticket guidelines and explain the ticket creation reason in detail so our staff can help you.",color=discord.Colour.blurple())
            await ticket_channel.send(mention_member,embed=creation_embed) # Mentions the member and sends the embded to the channel where the ticket is created.


@client.command()
async def close(ctx):
    channel = ctx.channel
    if channel.name.startswith("ticket"): #checks if a channel name starts with "ticket"
        await ctx.reply("Are you sure you want to close the ticket? Reply with ``confirm`` to close the ticket.") #Will ask the user to confirm to close the ticket
        await client.wait_for("message",check=lambda  m: m.channel == ctx.channel and m.author == ctx.author and m.content == "confirm",timeout=10) #Wait for a message with content "confirm" and makes sure that the command runner is the message sender and waits for reply for 10 seconds.
        await channel.delete() #If the message is "confirm" it will delete the channel
        closer = ctx.author.mention 
        transcript_chan = client.get_channel(803399751487717396) #channel to send the ticket transcript to.
        await transcript_chan.send(closer,file=discord.File(f"tickets/{channel.id}.txt")) #Sends the file to the transcript channel and mentions the ticket closer there.
    else:
        return

@client.command()
@commands.is_owner()
async def config(ctx, msg: discord.Message=None, category: discord.CategoryChannel=None): #Usage =  !config "message_id category_id" to get the ids enable deveoper mode and right click the message that will be used to create tickets and the category id is the category where the tickets will be created.
    if msg is None or category is None: #If a message id or category id is not provided.
        error_embed=discord.Embed(title="Ticket Configuration Failed",description="Failed to configure. Either an argument is missing or an invalid argument was passed.",color=discord.Colour.red())
        await ctx.channel.send(embed=error_embed)
        return

    client.ticket_configs[ctx.guild.id] = [msg.id, msg.channel.id, category.id] #Resets the configuration

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        data = await file.readlines()

    async with aiofiles.open("ticket_configs.txt", mode="w") as file:
        await file.write(f"{ctx.guild.id} {msg.id} {msg.channel.id} {category.id}\n")

        for line in data:
            if int(line.split(" ")[0]) != ctx.guild.id:
                await file.write(line)

    await msg.add_reaction(u"\U0001F3AB") # Adds reaction to the message and when someone reacts to this emoji it will create a ticket.
    await ctx.channel.send("Successfully configured the ticket system.") # If you get thsi it means that the ticket system has been configured successfully.

@client.event
async def on_message(message):
    await client.process_commands(message)#processes the command
    if message.channel.name.startswith("ticket"): #check if the channel name starts with "ticket"
        f = open(f"tickets/{message.channel.id}.txt", "a") # Opens the channel id in the tickets folder
        f.write(f"{message.author} : {message.content}\n") # Write the message author and the message he sent
        f.close() #closesthe file
        
client.run("your_bot_token_here")
