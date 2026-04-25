import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extractor_args': {'youtube': ['player_client=android,web']},
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dicionário para armazenar as filas por servidor
queues = {}

def check_queue(ctx):
    """Verifica se há mais músicas na fila e toca a próxima"""
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        next_song = queues[ctx.guild.id].pop(0)
        url = next_song['url']
        title = next_song['title']
        
        # Cria a fonte de áudio
        source = discord.FFmpegOpusAudio(url, **FFMPEG_OPTIONS)
        
        # Toca a música e chama esta mesma função ao terminar (loop de fila)
        ctx.voice_client.play(source, after=lambda e: check_queue(ctx))
        
        # Envia mensagem avisando a próxima (precisa ser via threadsafe no callback 'after')
        coro = ctx.send(f"🎶 Tocando agora: **{title}**")
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            fut.result()
        except:
            pass

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Entre em um canal de voz primeiro!")

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                song_data = {'url': info['url'], 'title': info['title']}
            except Exception as e:
                return await ctx.send(f"❌ Erro ao buscar: {e}")

        # Se já estiver tocando, adiciona na fila
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            if ctx.guild.id not in queues:
                queues[ctx.guild.id] = []
            queues[ctx.guild.id].append(song_data)
            return await ctx.send(f"✅ Adicionado à fila: **{song_data['title']}**")
        
        # Se não estiver tocando, toca imediatamente
        source = await discord.FFmpegOpusAudio.from_probe(song_data['url'], **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=lambda e: check_queue(ctx))
        await ctx.send(f"🎶 Tocando agora: **{song_data['title']}**")

@bot.command()
async def skip(ctx):
    """Pula a música atual (funciona mesmo se estiver pausado)"""
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        ctx.voice_client.stop()  # Isso interrompe o áudio atual e dispara o check_queue
        await ctx.send("⏭️ Música pulada!")
    else:
        await ctx.send("❌ Não há nenhuma música tocando no momento.")

@bot.command()
async def queue(ctx):
    """Mostra as próximas músicas"""
    if ctx.guild.id not in queues or not queues[ctx.guild.id]:
        return await ctx.send("📁 A fila está vazia.")
    
    lista = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(queues[ctx.guild.id])])
    await ctx.send(f"📜 **Fila de reprodução:**\n{lista}")

@bot.command()
async def stop(ctx):
    if ctx.guild.id in queues:
        queues[ctx.guild.id] = [] # Limpa a fila ao parar
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Tchau!")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Pausado")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Continuando")

bot.run(TOKEN)