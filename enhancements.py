# enhancements.py - attached enhancements for bot
import asyncio, os, json, tempfile, logging
from discord.ext import commands
import discord
from duckduckgo_search import ddg_answers, ddg
import yt_dlp
logger = logging.getLogger("enhancements")

try:
    from bot import bot
except Exception:
    try:
        from bot_core import bot
    except Exception:
        bot = globals().get("bot", None)

if bot is None:
    logger.error("No bot object found to attach enhancements.")
else:
    settings_path = "personality_settings.json"
    if not os.path.exists(settings_path):
        with open(settings_path,"w") as f:
            json.dump({"default_personality":"friendly","per_guild":{}}, f)

    def load_personality(guild_id):
        try:
            with open(settings_path,"r") as f:
                data = json.load(f)
            return data.get("per_guild",{}).get(str(guild_id), data.get("default_personality","friendly"))
        except:
            return "friendly"
    def set_personality(guild_id, p):
        try:
            with open(settings_path,"r") as f:
                data=json.load(f)
        except:
            data={"default_personality":"friendly","per_guild":{}}
        data.setdefault("per_guild",{})[str(guild_id)]=p
        with open(settings_path,"w") as f:
            json.dump(data,f)

    statuses = ["🎬 Helping editors | !list","AI-powered 🤖","Serving {guilds} servers","Watching tutorials"]
    async def status_rotator():
        await bot.wait_until_ready()
        import random
        while not bot.is_closed():
            try:
                guilds = len(bot.guilds) if bot.guilds else 0
                status = random.choice(statuses).format(guilds=guilds)
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,name=status))
            except Exception as e:
                logger.error("status_rotator error: %s", e)
            await asyncio.sleep(18)

    @bot.command(name="search", help="Search via DuckDuckGo")
    async def search_cmd(ctx, *, query: str=None):
        if not query:
            return await ctx.reply("Usage: `!search some query`")
        await ctx.trigger_typing()
        try:
            answers = ddg_answers(query, region='wt-wt', safesearch='Moderate', timelimit=10)
            if answers:
                out = "\\n".join(f"- {a}" for a in answers[:5])
                return await ctx.reply(f"**Quick answers:**\\n{out}")
            results = ddg(query, max_results=5)
            if results:
                lines=[]
                for r in results[:5]:
                    title=r.get('title') or r.get('text')[:60]
                    url=r.get('href') or r.get('url')
                    snippet=(r.get('body') or r.get('text') or "")[:180]
                    lines.append(f"**{title}**\\n{snippet}\\n<{url}>\\n")
                return await ctx.reply("\\n".join(lines))
            return await ctx.reply("No results found.")
        except Exception as e:
            logger.error("search error: %s", e)
            await ctx.reply(f"Search failed: {e}")

    @bot.command(name="yt", help="Download YouTube video/audio: !yt video <url> or !yt audio <url>")
    async def yt_cmd(ctx, mode: str=None, url: str=None):
        if not mode or not url:
            return await ctx.reply("Usage: `!yt video <url>` or `!yt audio <url>`")
        await ctx.reply("Processing...")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                if mode.lower()=="audio":
                    opts={"format":"bestaudio/best","outtmpl":f"{tmpdir}/audio.%(ext)s","quiet":True,"noplaylist":True}
                else:
                    opts={"format":"best","outtmpl":f"{tmpdir}/video.%(ext)s","quiet":True,"noplaylist":True}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info=ydl.extract_info(url, download=True)
                    filename=ydl.prepare_filename(info)
                size=os.path.getsize(filename)
                if size <= 8*1024*1024:
                    await ctx.author.send(file=discord.File(filename))
                    await ctx.reply("Sent file to your DMs.")
                else:
                    await ctx.reply(f"Downloaded but file is {size/(1024*1024):.1f}MB which is too large to send via Discord. Use external download.")
        except Exception as e:
            logger.error("yt error: %s", e)
            await ctx.reply(f"Download failed: {e}")

    @bot.command(name="setpersonality", help="Set server personality (admin only)")
    @commands.has_guild_permissions(administrator=True)
    async def set_personality_cmd(ctx, personality: str=None):
        if not personality:
            return await ctx.reply("Provide: friendly, sarcastic, professional, hype")
        allowed=["friendly","sarcastic","professional","hype","gangster","romantic"]
        if personality.lower() not in allowed:
            return await ctx.reply(f"Unknown. Allowed: {', '.join(allowed)}")
        set_personality(ctx.guild.id, personality.lower())
        await ctx.reply(f"Personality set to {personality.lower()}")

    @bot.command(name="personality", help="Show current personality")
    async def show_personality_cmd(ctx):
        p = load_personality(ctx.guild.id) if ctx.guild else "friendly"
        await ctx.reply(f"Current personality: {p}")

    # auto-moderation simple listener
    def contains_toxic(text):
        txt = text.lower()
        bad = ['kys','kill yourself','go die','i hope you die','fuck off','fuck you']
        for b in bad:
            if b in txt:
                return True, b
        return False, None

    async def moderation_listener(message):
        try:
            if message.author == bot.user or message.author.bot:
                return
            if not message.guild:
                return
            toxic, reason = contains_toxic(message.content)
            if toxic:
                if message.guild.me.guild_permissions.moderate_members:
                    from datetime import datetime, timedelta
                    until = datetime.utcnow() + timedelta(minutes=10)
                    await message.author.timeout(until, reason="Auto moderation")
                    await message.channel.send(f"🔇 {message.author.mention} has been timed out for toxic language.")
                else:
                    await message.channel.send("Detected toxic language but lacking permissions to timeout.")
        except Exception as e:
            logger.error("mod listener error: %s", e)

    # attach listeners and start rotator on ready
    bot.add_listener(moderation_listener, "on_message")
    bot.add_listener(lambda: None, "on_message")  # placeholder to avoid duplicates
    async def start_enh():
        if getattr(bot, "_enh_started", False):
            return
        bot._enh_started = True
        bot.loop.create_task(status_rotator())
        logger.info("Enhancements started")
    bot.add_listener(lambda: asyncio.ensure_future(start_enh()), "on_ready")
