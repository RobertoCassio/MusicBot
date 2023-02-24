import asyncio
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import discord
from discord.ext import commands
import time
import textwrap

from yt_dlp import YoutubeDL


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.music_name = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}  # Não pega áudio de playlist
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
                print(f"URL: {info['formats'][3]['url']}")

            except Exception:
                return False
        return {'source': info['formats'][3]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']  # Pega a primeira URL

            self.music_queue.pop(0)

            self.vc.play(
                discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=m_url, **self.FFMPEG_OPTIONS),
                after=lambda e: self.play_next())

        else:
            self.is_playing = False
            asyncio.create_task(self.leave_away())

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

            if self.vc == None:
                await ctx.send("Não estou conseguindo me conectar ao canal de voz meu bom. ")
                return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            song_name = self.music_queue[0][0]['title']
            self.music_name = song_name
            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())

            await ctx.send(f"Tocando Agora: {song_name}")
        else:
            self.is_playing = False
            asyncio.create_task(self.leave_away(ctx))

    @commands.command(name="play", aliases=['p', 'tocar'], help="Toca a música que tu quer uai")
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Conecte-se a um canal de voz")

        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Não consegui baixar a música, tente outra palavra chave meu bom.")
            else:
                await ctx.send("Música adicionada a fila.")
                self.music_queue.append([song, voice_channel])
                if self.is_playing == False:
                    await self.play_music(ctx)
                    asyncio.create_task(self.leave_away(ctx))

    @commands.command(name="pause", aliases=['parar', 'stop'], help="Para a música? lol")
    async def pause(self, ctx):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()

            await ctx.send("A música foi pausada.")
            asyncio.create_task(self.leave_away(ctx))

        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
            await ctx.send("A música voltou a tocar.")

    @commands.command(name="resume", aliases=['r', 'continuar'], help="Continua o que tava tocando")
    async def resume(self, ctx):
        if self.is_paused:
            self.is_playing = False
            self.is_paused = True
            self.vc.resume()

    @commands.command(name="skip", aliases=['pular'], help="Pula a música atual.")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            await self.play_music(ctx)

    @commands.command(name="queue", aliases=["q", "fila"], help="Mostra músicas na fila.")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            if i > 4: break
            retval += self.music_queue[i][0]['title'] + '\n'
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("Nenhuma música na fila")

    @commands.command(name="clear", aliases=['c'], help="Limpa a fila.")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Fila de música limpa!")

    @commands.command(name="leave", aliases=["sair"], help="Retira o bot do canal.")
    async def leave(self, *args):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()

    @commands.command(name="lyrics", aliases=['letras', 'l', 'letra'], help="Mostra a letra da música.")
    async def lyrics(self, ctx):
        print("Lyrics chamado")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        drive = webdriver.Chrome(options=options)
        print("WebDriver Aberto")

        print('chamando a música')

        drive.get('https://www.letras.mus.br/')
        print("Entrando no letras")
        elem = drive.find_element(By.ID, 'main_suggest')
        elem.clear()
        elem.send_keys(self.music_name)
        elem.send_keys(Keys.ENTER)
        print("Busca feita com sucesso")

        elem = drive.find_element(By.XPATH,
                                  '/html/body/div[1]/div[1]/div[1]/div[3]/div/div/div/div/div/div/div/div[5]/div['
                                  '2]/div/div/div[1]/div[1]/div[1]/div[1]/div/a')
        elem.click()
        print("Página encontra com sucesso")

        try:
            letra = drive.find_element(By.CLASS_NAME, 'cnt-letra').text
        except NoSuchElementException:
            letra = drive.find_element(By.CLASS_NAME, 'cnt-trad_l ').text

        print(f'Segue a letra: \n{letra}')
        chunks = textwrap.wrap(letra, width=2000, replace_whitespace=False)
        await ctx.send("Segue a letra:")
        for chunk in chunks:
            await ctx.send(chunk)

    async def leave_away(self, ctx):
        if self.is_playing and self.is_paused:
            print("Voice is playing, returning...")
            return
        print("Voice is not playing, continuing...")
        while True:
            await asyncio.sleep(10)

            if not self.is_playing:
                await asyncio.sleep(30)

                if not self.is_playing:
                    await ctx.send("Vazando por Inatividade! See Ya!")
                    await self.vc.disconnect()
                    break
