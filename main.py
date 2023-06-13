import asyncio
import datetime
from datetime import datetime as dt
import requests
import discord
import unicodedata
from discord.ext import commands
import ffmpeg
import os
import random


token = '4eeb56814b635a2b47d96771d700fb97'
dis_token = 'MTExMjM0MzI4Nzc0ODEwMDEzOA.GHXqXu.flJ1xD-svcf8g2DvV9wKyXLcryGyHu0leq6Mq0'


async def get_weather(city):
    request = requests.get("https://api.openweathermap.org/data/2.5/weather",
                           params={
                               'q': city,
                               'appid': token,
                               'units': 'metric',
                               'lang': 'ru'
                           })
    data = request.json()
    return data


class WeatherButtons(discord.ui.View):
    sky = ""
    temp = ""
    wind = ""
    emojis = {
        '01d': "☀️",
        '02n': "🌤️",
        '03d': "⛅",
        '04d': "⛅",
        '09d': "🌦️",
        '10d': "🌧️",
        '11d': "⛈️",
        '13d': "❄️",
    }
    now_emoji = ""

    def __init__(self, ctx, city):
        super().__init__(timeout=20.0)
        self.city = city
        self.ctx = ctx

    async def get_data(self, city):
        data = await get_weather(city)
        self.sky = "{0}\nДавление {1} мм.рт.ст".format(data['weather'][0]['description'],  data['main']['pressure'])
        self.temp = "{0}°C\nОщущается как {1}°C".format(data['main']['temp'], data['main']['feels_like'])
        self.wind = "Ветер {0} м/с".format(data['wind']['speed'])
        self.now_emoji = self.emojis[data['weather'][0]['icon']] if data['weather'][0]['icon'] in self.emojis else ""

    @discord.ui.button(label="Небо", emoji="🌈", style=discord.ButtonStyle.green)
    async def sky_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_data(self.city)
        await interaction.response.send_message(self.sky+self.now_emoji, delete_after=10)
        await write_log(self.ctx, self.sky+self.now_emoji)

    @discord.ui.button(label="Температура", emoji="🌡", style=discord.ButtonStyle.green)
    async def temp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_data(self.city)
        await interaction.response.send_message(self.temp, delete_after=10)
        await write_log(self.ctx, self.temp)

    @discord.ui.button(label="Ветер", emoji="🌪", style=discord.ButtonStyle.green)
    async def wind_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_data(self.city)
        await interaction.response.send_message(self.wind, delete_after=10)
        await write_log(self.ctx, self.wind)


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f"Bot {bot.user} is ready!")


async def short_message(ctx, answer, view=None):
    await write_log(ctx, answer)
    await ctx.message.delete(delay=15)
    await ctx.send(answer, delete_after=15, view=view)





@bot.event
async def on_command_error(ctx, error):
    print(error)
    try:
        answer = f"Делай так: '{ctx.prefix}{ctx.command.name}' (аргумент)"
    except:
        answer = "Такой команды нет!"
    await short_message(ctx, answer)


@bot.command(name="погода", brief="     Shows weather")
async def weather(ctx, city):
    view = WeatherButtons(ctx, city)
    await short_message(ctx, answer="", view=view)



def replace_non_ascii(text):
    return ''.join(c if ord(c) < 128 else unicodedata.normalize('NFKD', c).encode('ascii', 'ignore').decode('ascii') for c in text)


async def write_log(ctx, answer):
    member = ctx.message.author.display_name
    with open(f"{member}.txt", "a") as f:
        f.write(replace_non_ascii(f"{ctx.message.content}\n{answer}\n{dt.now()}\n\n"))



@bot.command(name="Закат", brief="     Shows time untill sunset")
async def when_sunset(ctx, city):
    data = await get_weather(city)
    sunset_unix = data['sys']['sunset']
    timezone_offset = data['timezone']
    sunset_utc = datetime.datetime.utcfromtimestamp(sunset_unix)
    sunset_time = sunset_utc + datetime.timedelta(seconds=timezone_offset)
    time_now = datetime.datetime.utcnow() + datetime.timedelta(seconds=timezone_offset)

    time_until_sunset = sunset_time - time_now
    hours, remainder = divmod(time_until_sunset.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    answer = "Закат в {0}\nДо него осталось {1}ч. {2}м.".format(sunset_time.strftime('%H:%M:%S'), hours, minutes)
    await short_message(ctx, answer)


@bot.command(name="Рассвет", brief="     Shows time untill sunrise")
async def when_sunset(ctx, city):
    data = await get_weather(city)
    sunset_unix = data['sys']['sunrise']
    timezone_offset = data['timezone']
    sunset_utc = datetime.datetime.utcfromtimestamp(sunset_unix)
    print()
    sunset_time = sunset_utc + datetime.timedelta(seconds=timezone_offset)
    time_now = datetime.datetime.utcnow() + datetime.timedelta(seconds=timezone_offset)

    time_until_sunset = sunset_time - time_now
    hours, remainder = divmod(time_until_sunset.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    answer = "Рассвет в {0}\nДо него осталось {1}ч. {2}м.".format(sunset_time.strftime('%H:%M:%S'), hours, minutes)
    await short_message(ctx, answer)


async def infinite_loop(ctx, voice, songs):
    global skip_song
    global stop_song
    global pause_song

    for song in songs:
        if stop_song:
            stop_song=False
            return
        while True:
            if pause_song:
                voice.pause()
                await asyncio.sleep(1)
                continue
            elif not pause_song and not voice.is_playing():
                voice.resume()
            if stop_song:
                await voice.disconnect()
                break
            if skip_song:
                voice.stop()
                skip_song = False
            if not voice.is_playing():
                voice.play(
                    discord.FFmpegPCMAudio(
                        executable="ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe",
                        source=song))
                await short_message(ctx, f"Playing {song}..")

                break
            else:
                await asyncio.sleep(1)

    await short_message(ctx, "Finished playing all songs.")
    await voice.disconnect()


async def play(ctx, name):
    global stop_song
    if ctx.voice_client is not None:
        stop_song = True
        await ctx.voice_client.disconnect()
    channel = ctx.author.voice.channel
    if channel is None:
        await ctx.send("Вы не подключены к голосовому каналу")
        return
    voice = await channel.connect()


    if name == "": name = ctx.message.author.display_name
    folder_path = f"music/{name}/"
    try:
        songs = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".mp3")]
    except:
        await short_message(ctx, f"У {name} еще нет музыки.")
        folder_path = f"music/K0TtiNk斯蒂勒/"
        songs = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".mp3")]
    return voice, songs


@bot.command(name="playall", brief="Воспроизводит музыку по порядку\nнеобязательный аргумент: ник")
async def play_all(ctx, *, name=""):
    voice, songs = await play(ctx, name)
    await infinite_loop(ctx, voice, songs)


@bot.command(name="playrandom", brief="Воспроизводит музыку случайно\nнеобязательный аргумент: ник")
async def play_random(ctx, *, name=""):
    voice, songs = await play(ctx, name)
    random.shuffle(songs)
    await infinite_loop(ctx, voice, songs)


skip_song = False
stop_song = False
pause_song = False


@bot.command(name="skip")
async def skip(ctx):
    global skip_song
    skip_song = True
    await short_message(ctx, "skipping..")


@bot.command(name="pause")
async def pause(ctx):
    global pause_song
    pause_song = not pause_song
    if pause_song:
        await short_message(ctx, "pausing..")
    else:
        await short_message(ctx, "unpausing..")
    


@bot.command(name="stop")
async def stop(ctx):
    global stop_song
    stop_song = True
    await short_message(ctx, "disconnecting..")


def main():
    bot.run(dis_token)


main()










