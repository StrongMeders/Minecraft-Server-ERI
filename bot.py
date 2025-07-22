import os
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

class DiscordBot:
    def __init__(self):
        intents = discord.Intents.default()
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.mensagem = None

    def rodar(self, mensagem_texto):
        @self.bot.event
        async def on_ready():
            print(f"[Discord] Bot conectado como {self.bot.user}")
            canal = self.bot.get_channel(CHANNEL_ID)

            # Apaga a última mensagem do bot, se houver
            async for msg in canal.history(limit=20):
                if msg.author == self.bot.user:
                    await msg.delete()
                    break

            # Envia nova mensagem
            nova_msg = await canal.send(mensagem_texto)
            self.mensagem = nova_msg
            await self.bot.close()  # Encerra o bot após enviar

        asyncio.run(self.bot.start(TOKEN))
