import discord
import subprocess
import datetime
import os

# CONFIG
TOKEN = 'SEU_TOKEN_DISCORD_AQUI'
GITHUB_BRANCH = "main"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync()
    print(f'🤖 Bot conectado como {bot.user}!')

@tree.command(name="save-all", description="Finaliza servidor e salva no GitHub")
async def save_all(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Finalizando servidor e salvando...")
    
    # Enviar comando para o servidor encerrar
    subprocess.run(["screen", "-S", "minecraft", "-p", "0", "-X", "stuff", "say Salvando...^M"])
    subprocess.run(["screen", "-S", "minecraft", "-p", "0", "-X", "stuff", "stop^M"])

    # Esperar alguns segundos
    await interaction.followup.send("💾 Salvando alterações no GitHub...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"{timestamp}-I am the ALL RANGE"])
    subprocess.run(["git", "push", "origin", GITHUB_BRANCH])

    await interaction.followup.send("✅ Servidor salvo e backup feito com sucesso!")

bot.run(TOKEN)
