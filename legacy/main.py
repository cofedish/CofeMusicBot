import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Загружаем токен из .env файла
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    raise ValueError("Токен Discord не найден. Убедитесь, что .env файл содержит DISCORD_TOKEN.")

# Создаем объект Intents и объект бота с нужными интентами
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=',', intents=intents)

# Событие готовности бота
@bot.event
async def on_ready():
    print(f'{bot.user} подключился к Discord!')
    await load_cogs()  # Загружаем cogs при запуске

# Команда для перезагрузки Cogs
@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension: str):
    """Команда для перезагрузки указанного cog."""
    try:
        print(f"Получена команда reload {extension}")
        await bot.unload_extension(f'cogs.{extension}')  # Используем await
        await bot.load_extension(f'cogs.{extension}')  # Используем await
        await ctx.send(f'{extension} перезагружен.')
        print("Успех")
    except commands.ExtensionNotLoaded:
        await ctx.send(f'Cog {extension} не был загружен ранее.')
        print(f"Ошибка. Cog {extension} не был загружен ранее.")
    except commands.ExtensionNotFound:
        await ctx.send(f'Cog {extension} не найден.')
        print(f'Cog {extension} не найден.')
    except Exception as e:
        await ctx.send(f'Ошибка при перезагрузке {extension}: {str(e)}')
        print(f'Ошибка при перезагрузке {extension}: {str(e)}')

# Автоматическая загрузка всех Cogs из директории 'cogs'
async def load_cogs():
    cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
    if not os.path.exists(cogs_dir):
        raise FileNotFoundError(f"Папка 'cogs' не найдена в {os.path.dirname(__file__)}")

    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')  # Загружаем файл без расширения '.py'
                print(f'Cog {filename} загружен успешно.')
            except Exception as e:
                print(f'Ошибка при загрузке {filename}: {e}')

# Запуск бота
bot.run(TOKEN)
