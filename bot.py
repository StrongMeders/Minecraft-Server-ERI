import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

print(f"TOKEN carregado: {TOKEN}")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ultima_msg_id = None  # Será usada para armazenar e deletar a última mensagem

@bot.event
async def on_ready():
    print(f"[Bot] Conectado como {bot.user.name}")

    canal = bot.get_channel(CHANNEL_ID)
    if not canal:
        print("[Erro] Canal não encontrado. Verifique o ID.")
        return

    global ultima_msg_id

    # Apaga a última mensagem enviada pelo próprio bot, se existir
    async for msg in canal.history(limit=20):
        if msg.author == bot.user:
            ultima_msg_id = msg.id
            await msg.delete()
            print("[Bot] Mensagem anterior apagada.")
            break

    # Mensagem nova
    ip = "0.tcp.ngrok.io"
    porta = "19342"
    conteudo = f"""[Servidor Online]
ip: {ip}:{porta}"""

    nova_msg = await canal.send(conteudo)
    print(f"[Bot] Nova mensagem enviada: {nova_msg.id}")


if __name__ == "__main__":
    bot.run(TOKEN)