import os
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import asyncio
import concurrent.futures

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=',', intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': False,
    'verbose': True,
    'outtmpl': '%(id)s.%(ext)s',
    'noplaylist': True,  # Не загружаем плейлисты целиком, если это не требуется
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdl_format_options)
ffmpeg_executable = "C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe"

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current = None
        self.voice_client = None
        self.playlist = {}
        self.is_loading = False  # Флаг, чтобы отслеживать загрузку трека

    async def join_channel(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to use this command.")
            return False
        voice_channel = ctx.author.voice.channel
        if self.voice_client is None:
            self.voice_client = await voice_channel.connect()
        else:
            await self.voice_client.move_to(voice_channel)
        return True

    async def handle_playback_complete(self, ctx):
        await self.cleanup_file(self.current.source)
        await self.play_next(ctx)

    async def play_next(self, ctx):
        # Ensure the voice client is valid and no track is playing
        if not self.voice_client or not self.voice_client.is_connected():
            return

        if self.voice_client.is_playing():
            self.voice_client.stop()

        if len(self.queue) == 0 and not self.is_loading:
            await ctx.send("Очередь пуста. Покидаю голосовой канал.")
            await self.voice_client.disconnect()
            self.voice_client = None
            return

        # Fetch the next song from the queue and start playing
        if len(self.queue) > 0:
            self.current = self.queue.pop(0)
            await ctx.send(f"Сейчас играет: {self.current.title}")
            self.voice_client.play(self.current,
                                   after=lambda e: asyncio.run_coroutine_threadsafe(self.handle_playback_complete(ctx),
                                                                                    self.bot.loop))

            # Pre-fetch the next track while the current is playing
            if len(self.queue) > 0:
                await self.preload_next_track(ctx)

    async def preload_next_track(self, ctx):
        """Загружает следующий трек в фоне, пока текущий воспроизводится."""
        # Убедимся, что следующий элемент очереди все еще является заглушкой
        if isinstance(self.queue[0], dict):
            next_query = self.queue[0]['query']  # Получаем исходный запрос
            loop = asyncio.get_event_loop()

            # Используем отдельный поток для загрузки следующего трека
            with concurrent.futures.ThreadPoolExecutor() as pool:
                data = await loop.run_in_executor(pool, lambda: ytdl.extract_info(next_query, download=True))
            video = data['entries'][0] if 'entries' in data else data
            filename = ytdl.prepare_filename(video)
            source = discord.FFmpegPCMAudio(filename, executable=ffmpeg_executable, **ffmpeg_options)
            source.title = video.get('title', 'Unnamed track')
            source.source = filename

            # Заменяем заглушку треком в очереди, только если она не была заменена
            if isinstance(self.queue[0], dict) and self.queue[0].get("loading"):
                self.queue[0] = source

    async def add_to_queue(self, ctx, query):
        if not await self.join_channel(ctx):
            return

        # Если запрос не является ссылкой, ищем на YouTube
        if not query.startswith("http"):
            query = f"ytsearch:{query}"

        # Добавляем трек в очередь
        self.queue.append({"loading": True, "title": "Loading...", "query": query})
        self.is_loading = True

        loop = asyncio.get_event_loop()

        try:
            # Используем отдельный поток для загрузки трека
            with concurrent.futures.ThreadPoolExecutor() as pool:
                data = await loop.run_in_executor(pool, lambda: ytdl.extract_info(query, download=True))
            video = data['entries'][0] if 'entries' in data else data
            filename = ytdl.prepare_filename(video)
            source = discord.FFmpegPCMAudio(filename, executable=ffmpeg_executable, **ffmpeg_options)
            source.title = video.get('title', 'Unnamed track')
            source.source = filename

            # Заменяем заглушку треком в очереди
            for i, item in enumerate(self.queue):
                if isinstance(item, dict) and item.get("loading"):
                    self.queue[i] = source
                    break

            await ctx.send(f"Добавлено в очередь: {video['title']}")

            # Если ничего не играет, начинаем воспроизведение
            if not self.voice_client.is_playing():
                await self.play_next(ctx)

        except Exception as e:
            await ctx.send(f"Произошла ошибка: {str(e)}")

        finally:
            self.is_loading = False

    async def skip(self, ctx):
        """Пропускает текущий трек."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()

        # Проверяем, если загружается следующий трек
        if self.is_loading:
            await ctx.send("Текущий трек еще загружается. Попробуйте еще раз после завершения загрузки.")

        await self.play_next(ctx)


    async def stop(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await self.cleanup_file(self.current.source)
            self.queue.clear()  # Очищаем очередь
            await self.voice_client.disconnect()
            self.voice_client = None
            self.current = None

    async def skip(self, ctx):
        """Skip the current track."""
        if not self.voice_client or not self.voice_client.is_playing():
            await ctx.send("Нет трека для пропуска.")
            return

        # Stop the current track and move to the next one
        self.voice_client.stop()
        await self.play_next(ctx)

    async def pause(self):
        if self.voice_client.is_playing():
            self.voice_client.pause()

    async def resume(self):
        if self.voice_client.is_paused():
            self.voice_client.resume()

    async def create_playlist(self, ctx, playlist_name):
        if playlist_name in self.playlist:
            await ctx.send(f"Плейлист с именем {playlist_name} уже существует.")
        else:
            self.playlist[playlist_name] = []
            await ctx.send(f"Плейлист {playlist_name} успешно создан.")

    async def add_to_playlist(self, ctx, playlist_name, query):
        if playlist_name not in self.playlist:
            await ctx.send(f"Плейлист {playlist_name} не существует.")
            return

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
        self.playlist[playlist_name].append(data['webpage_url'])
        await ctx.send(f"Трек {data['title']} добавлен в плейлист {playlist_name}.")

    async def play_playlist(self, ctx, playlist_name):
        if playlist_name not in self.playlist:
            await ctx.send(f"Плейлист {playlist_name} не существует.")
            return

        for url in self.playlist[playlist_name]:
            await self.add_to_queue(ctx, url)

    async def cleanup_file(self, filename):
        """Удаляет файл из файловой системы."""
        try:
            if filename and os.path.exists(filename):
                await asyncio.sleep(3)  # Увеличиваем задержку для завершения работы ffmpeg
                os.remove(filename)
                print(f"File {filename} deleted successfully.")
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")


music_player = MusicPlayer(bot)

@bot.command(name='GOYDA', help='ГООООЙДАААА!!!!')
async def goyda(ctx):
    print(f"Command received: GOYDA")
    query = "https://rus.hitmotop.com/get/music/20230915/Okhlabystin_-_gojjda_76690131.mp3"
    await music_player.add_to_queue(ctx, query)

@bot.command(name='rickroll', help='Ну нажми че ты')
async def rick(ctx):
    print(f"Command received: rickroll")
    query = "https://rus.hitmotop.com/get/music/20170902/Rick_Astley_-_Never_Gonna_Give_You_Up_47958276.mp3"
    await music_player.add_to_queue(ctx, query)

@bot.command(name='play', help='Воспроизведение музыки')
async def play(ctx, *, query):
    print(f"Command received: play {query}")
    await music_player.add_to_queue(ctx, query)

@bot.command(name='stop', help='Остановить воспроизведение')
async def stop(ctx):
    print("Command received: stop")
    await music_player.stop()

@bot.command(name='skip', help='Пропустить текущий трек')
async def skip(ctx):
    print("Command received: skip")
    await music_player.skip(ctx)

@bot.command(name='pause', help='Поставить на паузу')
async def pause(ctx):
    print("Command received: pause")
    await music_player.pause()

@bot.command(name='resume', help='Возобновить воспроизведение')
async def resume(ctx):
    print("Command received: resume")
    await music_player.resume()

@bot.command(name='create_playlist', help='Создать плейлист')
async def create_playlist(ctx, playlist_name):
    print(f"Command received: create_playlist {playlist_name}")
    await music_player.create_playlist(ctx, playlist_name)

@bot.command(name='add_to_playlist', help='Добавить трек в плейлист')
async def add_to_playlist(ctx, playlist_name, *, query):
    print(f"Command received: add_to_playlist {playlist_name} {query}")
    await music_player.add_to_playlist(ctx, playlist_name, query)

@bot.command(name='play_playlist', help='Воспроизвести плейлист')
async def play_playlist(ctx, playlist_name):
    print(f"Command received: play_playlist {playlist_name}")
    await music_player.play_playlist(ctx, playlist_name)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


bot.run(TOKEN)
