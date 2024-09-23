import os

import discord
import asyncio
import concurrent.futures
from yt_dlp import YoutubeDL
from cache import LRUCache

ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': False,
    'outtmpl': 'cache/%(id)s.%(ext)s',
    'noplaylist': True,
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdl_format_options)
ffmpeg_executable = "C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe"

class MusicPlayer():
    def __init__(self, bot, voice_client=None):
        self.bot = bot
        self.queue = []
        self.current = None
        self.voice_client = voice_client
        self.cache = LRUCache('cache', max_size_gb=5)
        self.lock = asyncio.Lock()
        self.inactivity_task = None  # Задача для отслеживания простоя

    async def join_channel(self, ctx):
        """Присоединение к голосовому каналу пользователя."""
        if ctx.author.voice is None:
            await ctx.send("Вы должны быть в голосовом канале, чтобы использовать эту команду.")
            return False

        voice_channel = ctx.author.voice.channel

        # Проверяем, подключен ли бот к тому же каналу
        if self.voice_client and self.voice_client.is_connected() and self.voice_client.channel == voice_channel:
            return True  # Бот уже подключен к нужному каналу

        # Если бот подключен к другому каналу, перемещаем его
        if self.voice_client and self.voice_client.is_connected() and self.voice_client.channel != voice_channel:
            await self.voice_client.move_to(voice_channel)
        else:
            # Если бот не подключен, подключаемся
            await ctx.send("Здарова черти")
            self.voice_client = await voice_channel.connect()

        return True

    async def play_next(self, ctx):
        """Воспроизведение следующего трека."""
        async with self.lock:
            if not self.voice_client or not self.voice_client.is_connected():
                return

            if len(self.queue) == 0:
                await ctx.send("Очередь пуста. Покидаю голосовой канал.")
                await self.disconnect_from_channel()
                return

            self.current = self.queue.pop(0)
            await ctx.send(f"Сейчас играет: {self.current.title}")
            self.voice_client.play(self.current,
                                   after=lambda e: asyncio.run_coroutine_threadsafe(self.track_finished(ctx), self.bot.loop))

            await ctx.send(f"Осталось треков в очереди: {len(self.queue)}")

            if self.inactivity_task:
                self.inactivity_task.cancel()
                self.inactivity_task = None

    async def track_finished(self, ctx):
        """Обработчик завершения трека, который вызывает play_next."""
        if len(self.queue) > 0:
            await self.play_next(ctx)
        else:
            await ctx.send("Трек завершён, треков в очереди больше нет.")
            self.inactivity_task = asyncio.create_task(self.disconnect_after_inactivity(ctx))

    async def add_to_queue(self, ctx, query):
        """Добавление трека в очередь."""
        if not await self.join_channel(ctx):
            return

            # Если query — это путь к локальному файлу, добавляем его напрямую
        if os.path.isfile(query):
            source = discord.FFmpegPCMAudio(query, executable=ffmpeg_executable, **ffmpeg_options)
            source.title = os.path.basename(query)
            self.queue.append(source)
            await ctx.send(f"Локальный трек добавлен в очередь: {source.title}")

            if not self.voice_client.is_playing():
                await self.play_next(ctx)

            return

        if not query.startswith("http"):
            query = f"ytsearch:{query}"

        loop = asyncio.get_event_loop()

        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                data = await loop.run_in_executor(pool, lambda: ytdl.extract_info(query, download=True))
            video = data['entries'][0] if 'entries' in data else data
            filename = ytdl.prepare_filename(video)
            source = discord.FFmpegPCMAudio(filename, executable=ffmpeg_executable, **ffmpeg_options)
            source.title = video.get('title', 'Unnamed track')
            source.author = video.get('uploader', 'Unknown author')

            self.queue.append(source)
            await ctx.send(f"Трек добавлен в очередь: {source.author} - {source.title}")

            if not self.voice_client.is_playing():
                await self.play_next(ctx)

            await ctx.send(f"Всего треков в очереди: {len(self.queue)}")

            if self.inactivity_task:
                self.inactivity_task.cancel()
                self.inactivity_task = None

        except Exception as e:
            await ctx.send(f"Произошла ошибка: {str(e)}")


    async def skip(self, ctx):
        """Пропуск текущего трека."""
        async with self.lock:
            if not self.voice_client or not self.voice_client.is_playing():
                await ctx.send("Нет трека для пропуска.")
                return

            self.voice_client.stop()
            await ctx.send(f"Текущий трек пропущен. Осталось треков в очереди: {len(self.queue)}")


    async def stop(self, ctx):
        """Остановка воспроизведения и очистка очереди."""
        async with self.lock:
            if self.voice_client and self.voice_client.is_playing():
                self.voice_client.stop()
            self.queue.clear()
            await self.disconnect_from_channel()
            await ctx.send("Воспроизведение остановлено и очередь очищена.")

    async def disconnect_from_channel(self):
        """Отключение бота от голосового канала."""
        if self.voice_client:
            await self.voice_client.disconnect()
        self.voice_client = None
        self.current = None

    async def disconnect_after_inactivity(self, ctx):
        """Отключение через минуту, если ничего не играет."""
        await asyncio.sleep(60)
        if not self.voice_client.is_playing() and len(self.queue) == 0:
            await ctx.send("Ничего не воспроизводится в течение минуты. Покидаю канал.")
            await self.disconnect_from_channel()

def setup(bot):
    bot.add_cog(MusicPlayer(bot))
