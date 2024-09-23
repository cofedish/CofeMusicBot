import importlib
import asyncio
import os

from discord.ext import commands
import music_player  # Импортируем модуль music_player
from collections import deque


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_player = music_player.MusicPlayer(bot, bot.voice_clients[0] if bot.voice_clients else None)

        # Очередь для команд
        self.command_queue = deque()
        self.is_processing = False  # Флаг для отслеживания выполнения команд
        self.bot.loop.create_task(self.process_commands())  # Запуск обработчика очереди

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Логирование команды, введённой пользователем."""
        print(f"Команда {ctx.command} была введена пользователем {ctx.author} в канале {ctx.channel}", flush=True)

    # Добавляем команды в очередь
    async def add_to_command_queue(self, ctx, command):
        """Добавляем команду в очередь и выводим её в лог."""
        print(f"Добавляем команду {command.__name__} в очередь от {ctx.author}.", flush=True)
        self.command_queue.append((ctx, command))

    # Асинхронный обработчик очереди
    async def process_commands(self):
        """Асинхронный процесс обработки команд из очереди."""
        while True:
            if self.command_queue and not self.is_processing:
                self.is_processing = True  # Устанавливаем флаг обработки
                ctx, command = self.command_queue.popleft()  # Извлекаем команду из очереди
                try:
                    await command(ctx)  # Выполняем команду и ожидаем её завершения
                except Exception as e:
                    print(f"Ошибка при выполнении команды: {str(e)}", flush=True)
                self.is_processing = False  # Сбрасываем флаг после завершения
            await asyncio.sleep(0.1)  # Короткая пауза для предотвращения перегрузки цикла

    # Обертываем команды для их добавления в очередь
    @commands.command(name='play', help='Воспроизведение музыки')
    async def play(self, ctx, *, query):
        await self.add_to_command_queue(ctx, lambda ctx: self.music_player.add_to_queue(ctx, query))

    @commands.command(name='GOYDA', help='ГООООЙДАААА!!!!')
    async def goyda(self, ctx):
        query = r"cache\\Okhlabystin_-_gojjda_76690131.mp3" if os.name == 'nt' else "/cache/Okhlabystin_-_gojjda_76690131.mp3"
        await self.add_to_command_queue(ctx, lambda ctx: self.music_player.add_to_queue(ctx, query))

    @commands.command(name='rickroll', help='Ну нажми че ты')
    async def rick(self, ctx):
        query = r"cache\\Rick_Astley_-_Never_Gonna_Give_You_Up_47958276.mp3" if os.name == 'nt' else "/cache/Rick_Astley_-_Never_Gonna_Give_You_Up_47958276.mp3"
        await self.add_to_command_queue(ctx, lambda ctx: self.music_player.add_to_queue(ctx, query))

    @commands.command(name='skip', help='Пропустить текущий трек')
    async def skip(self, ctx):
        await self.add_to_command_queue(ctx, self.music_player.skip)

    @commands.command(name='stop', help='Остановить воспроизведение')
    async def stop(self, ctx):
        await self.add_to_command_queue(ctx, self.music_player.stop)

    @commands.command(name='reload_player', help='Перезагрузить логику музыкального плеера')
    @commands.has_permissions(administrator=True)
    async def reload_player(self, ctx):
        """Команда для перезагрузки модуля music_player."""
        await self.add_to_command_queue(ctx, self.reload_player_internal)

    async def reload_player_internal(self, ctx):
        try:
            importlib.reload(music_player)  # Перезагружаем модуль music_player
            self.music_player = music_player.MusicPlayer(self.bot,
                                                         self.bot.voice_clients[0] if self.bot.voice_clients else None)
            await ctx.send("Модуль music_player успешно перезагружен.")
        except Exception as e:
            await ctx.send(f"Произошла ошибка при перезагрузке music_player: {str(e)}")


async def setup(bot):
    await bot.add_cog(MusicCog(bot))
