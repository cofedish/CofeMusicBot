from music_player import MusicPlayer
"""
def setup_commands(bot):
    # Инициализируем плеер музыки
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
        print(f"Получена команда play: {query}")
        await music_player.add_to_queue(ctx, query)

    @bot.command(name='skip', help='Пропустить текущий трек')
    async def skip(ctx):
        print("Получена команда skip")
        await music_player.skip(ctx)

    @bot.command(name='stop', help='Остановить воспроизведение')
    async def stop(ctx):
        print("Получена команда stop")
        await music_player.stop(ctx)
"""