import os
import getpass
import subprocess
from pyngrok import ngrok, conf
from dotenv import load_dotenv, find_dotenv
import asyncio
import discord
from datetime import datetime

# --- Códigos ANSI para Cores ---
# Reset de cor
RESET = "\033[0m"

# Cores de texto (foreground)
ORANGE_GIT = "\033[38;5;208m"
DISCORD_BLUE = "\033[38;5;63m"
NGROK_BLUE = "\033[38;5;27m"
MINECRAFT_GREEN = "\033[32m"
CRIMSON_RED = "\033[38;5;124m"

# --- Carrega as variáveis do .env ---
load_dotenv(override=True, dotenv_path=find_dotenv())

# --- CONFIGURAÇÕES ---
SERVER_DIR = os.path.join(os.getcwd(), "server")
SERVER_JAR = "server.jar"
MINECRAFT_PORT = 25565
SAVE_INTERVAL_MINUTES = 15

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# --- Depuração de Carregamento de Variáveis ---
print(f"{DISCORD_BLUE}🔑 TOKEN lido: {RESET}{TOKEN}")
print(f"{DISCORD_BLUE}🆔 CHANNEL_ID lido: {RESET}{CHANNEL_ID}")

# --- Variáveis Globais ---
ip_global = None
port_global = None
minecraft_process = None

# --- Cliente Discord Global ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# --- Funções Git ---
def git_sync():
    print(f"{ORANGE_GIT}🔄 [Git]{RESET} Sincronizando repositório com origin/main...")
    try:
        subprocess.run("git fetch origin", shell=True, cwd=os.getcwd(), check=True)
        subprocess.run("git reset --hard origin/main", shell=True, cwd=os.getcwd(), check=True)
        print(f"{ORANGE_GIT}✅ [Git]{RESET} Repositório sincronizado com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"{ORANGE_GIT}❌ [Git]{RESET} Erro ao sincronizar: {e}")
        exit(1)

def git_push(usuario):
    print(f"{ORANGE_GIT}⬆️ [Git]{RESET} Fazendo commit e push do backup...")
    datahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    msg_commit = f"{datahora}-{usuario}"
    try:
        subprocess.run("git add .", shell=True, cwd=os.getcwd(), check=True)
        subprocess.run(f'git commit -m "{msg_commit}"', shell=True, cwd=os.getcwd(), check=True)
        subprocess.run("git push", shell=True, cwd=os.getcwd(), check=True)
        print(f"{ORANGE_GIT}📦 [Git]{RESET} Backup enviado!")
    except subprocess.CalledProcessError as e:
        print(f"{ORANGE_GIT}⚠️ [Git]{RESET} Erro ao fazer commit/push: {e}")
    except Exception as e:
        print(f"{ORANGE_GIT}🔥 [Git]{RESET} Erro inesperado no Git Push: {e}")

# --- Iniciar Ngrok ---
def iniciar_ngrok():
    print(f"{NGROK_BLUE}🌐 [Ngrok]{RESET} Iniciando túnel TCP via pyngrok...")
    token = os.getenv("NGROK_AUTHTOKEN")
    if not token:
        print(f"{NGROK_BLUE}⛔ [Ngrok]{RESET} Token não encontrado nas variáveis de ambiente!")
        exit(1)

    conf.get_default().auth_token = token
    tcp_tunnel = ngrok.connect(addr=MINECRAFT_PORT, proto="tcp")
    url = tcp_tunnel.public_url
    host, port = url.replace("tcp://", "").split(":")

    print(f"\n{MINECRAFT_GREEN}🌍 [Servidor Online]{RESET}")
    print(f"   IP: {host}:{port}\n")

    return host, port

# --- Bot Discord (on_ready para mensagem online inicial) ---
@client.event
async def on_ready():
    print(f"{DISCORD_BLUE}🤖 [Bot]{RESET} Logado como {CRIMSON_RED}{client.user}{RESET}.")
    canal = client.get_channel(CHANNEL_ID)
    if canal is None:
        print(f"{DISCORD_BLUE}🚫 [Erro]{RESET} Canal não encontrado.")
        return

    async for msg in canal.history(limit=20):
        if msg.author == client.user:
            await msg.delete()
            print(f"{DISCORD_BLUE}🗑️ [Bot]{RESET} Mensagem anterior apagada.")
            break

    await canal.send(f"✅ **[Servidor Online]**\n**IP:** `{ip_global}:{port_global}`")
    print(f"{DISCORD_BLUE}✉️ [Bot]{RESET} Mensagem enviada.")
    await asyncio.sleep(5)
    await client.close()
    print(f"{DISCORD_BLUE}👋 [Bot]{RESET} Cliente Discord finalizado.")

# --- Iniciar servidor Minecraft ---
def iniciar_server():
    global minecraft_process

    jar_path = os.path.join(SERVER_DIR, SERVER_JAR)
    print(f"{MINECRAFT_GREEN}⛏️ [Minecraft]{RESET} Tentando rodar o jar: {jar_path}")
    if not os.path.isfile(jar_path):
        print(f"{MINECRAFT_GREEN}🛑 [Erro]{RESET} Arquivo server.jar não encontrado no caminho esperado.")
        exit(1)

    minecraft_process = subprocess.Popen(
        f'java -jar "{jar_path}" nogui',
        cwd=SERVER_DIR,
        shell=True,
        stdin=subprocess.PIPE,
        text=True
    )
    return minecraft_process

# --- Auto-Save do Minecraft ---
async def auto_save_task():
    global minecraft_process

    print(f"{MINECRAFT_GREEN}⏳ [AutoSave]{RESET} Aguardando {SAVE_INTERVAL_MINUTES} minutos antes do primeiro save...")
    await asyncio.sleep(SAVE_INTERVAL_MINUTES * 60)

    while minecraft_process and minecraft_process.poll() is None:
        print(f"{MINECRAFT_GREEN}💾 [AutoSave]{RESET} Enviando comando /save-all para o servidor...")
        try:
            minecraft_process.stdin.write("save-all\n")
            minecraft_process.stdin.flush()
            print(f"{MINECRAFT_GREEN}✔️ [AutoSave]{RESET} Comando /save-all enviado.")
        except Exception as e:
            print(f"{MINECRAFT_GREEN}❌ [AutoSave]{RESET} Erro ao enviar comando /save-all: {e}")
            break

        await asyncio.sleep(SAVE_INTERVAL_MINUTES * 60)
    print(f"{MINECRAFT_GREEN}🏁 [AutoSave]{RESET} Tarefa de auto-save finalizada (servidor fechou).")

# --- Função Principal ---
async def main():
    global ip_global, port_global, minecraft_process

    usuario = getpass.getuser()
    git_sync()

    host, port = iniciar_ngrok()
    ip_global = host
    port_global = port

    print(f"{DISCORD_BLUE}🚀 [Bot]{RESET} Iniciando cliente Discord...")
    await client.start(TOKEN)

    print(f"{MINECRAFT_GREEN}▶️ [Minecraft]{RESET} Iniciando servidor...")
    minecraft_process = iniciar_server()

    auto_save_task_handle = asyncio.create_task(auto_save_task())

    await asyncio.to_thread(minecraft_process.wait)

    print(f"{MINECRAFT_GREEN}⏹️ [Minecraft]{RESET} Servidor Minecraft fechado.")

    if not auto_save_task_handle.done():
        auto_save_task_handle.cancel()
        try:
            await auto_save_task_handle
        except asyncio.CancelledError:
            print(f"{MINECRAFT_GREEN}↩️ [AutoSave]{RESET} Tarefa de auto-save cancelada.")

    git_push(usuario)

if __name__ == "__main__":
    if os.name == 'nt':
        os.system('color') # Ativa o processamento de sequências ANSI no Windows

    asyncio.run(main())