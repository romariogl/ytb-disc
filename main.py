import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio
from dotenv import load_dotenv

# Carrega o token do arquivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configurações do yt-dlp (Otimizado para 2026)
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # Previne erros de IPv6
}

# Opções do FFmpeg para evitar engasgos no stream
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot online como {bot.user}')

@bot.command()
async def play(ctx, *, search: str):
    """Toca uma música via link ou busca por nome"""
    if not ctx.author.voice:
        return await ctx.send("❌ Entre em um canal de voz primeiro!")

    # Conecta ao canal se não estiver conectado
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                url = info['url']
                title = info['title']
            except Exception as e:
                return await ctx.send(f"❌ Erro ao buscar: {e}")

        # Se já estiver tocando algo, para antes de começar a nova
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source)
        await ctx.send(f"🎶 Tocando agora: **{title}**")

@bot.command()
async def stop(ctx):
    """Para a música e desconecta"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Tchau!")

@bot.command()
async def pause(ctx):  # Adicionado 'async'
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Pausado") # Adicionado 'await'

@bot.command()
async def resume(ctx): # Adicionado 'async'
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Continuando") # Adicionado 'await'
        
bot.run(TOKEN)