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
ORANGE = "\033[38;5;208m"
DISCORD_BLUE = "\033[38;5;63m"
NGROK_BLUE = "\033[38;5;27m"
MINECRAFT_GREEN = "\033[32m"
CRIMSON_RED = "\033[38;5;124m"

# Cores em negrito (para maior destaque)
BOLD_ORANGE = "\033[1;38;5;208m"
BOLD_DISCORD_BLUE = "\033[1;38;5;63m"
BOLD_NGROK_BLUE = "\033[1;38;5;27m"
BOLD_MINECRAFT_GREEN = "\033[1;32m"
BOLD_CRIMSON_RED = "\033[1;38;5;124m"

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
print(f"{BOLD_DISCORD_BLUE}TOKEN lido: {TOKEN}{RESET}")
print(f"{BOLD_DISCORD_BLUE}CHANNEL_ID lido: {CHANNEL_ID}{RESET}")

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
    print(f"{BOLD_ORANGE}[Git] Sincronizando repositório com origin/main...{RESET}")
    try:
        subprocess.run("git fetch origin", shell=True, cwd=os.getcwd(), check=True)
        subprocess.run("git reset --hard origin/main", shell=True, cwd=os.getcwd(), check=True)
        print(f"{BOLD_ORANGE}[Git] Repositório sincronizado com sucesso!{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{ORANGE}[Git] Erro ao sincronizar: {e}{RESET}")
        exit(1)

def git_push(usuario):
    print(f"{BOLD_ORANGE}[Git] Fazendo commit e push do backup...{RESET}")
    datahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    msg_commit = f"{datahora}-{usuario}"
    try:
        subprocess.run("git add .", shell=True, cwd=os.getcwd(), check=True)
        subprocess.run(f'git commit -m "{msg_commit}"', shell=True, cwd=os.getcwd(), check=True)
        subprocess.run("git push", shell=True, cwd=os.getcwd(), check=True)
        print(f"{BOLD_ORANGE}[Git] Backup enviado!{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{ORANGE}[Git] Erro ao fazer commit/push: {e}{RESET}")
    except Exception as e:
        print(f"{ORANGE}[Git] Erro inesperado no Git Push: {e}{RESET}")

# --- Iniciar Ngrok ---
def iniciar_ngrok():
    print(f"{BOLD_NGROK_BLUE}[Ngrok] Iniciando túnel TCP via pyngrok...{RESET}")
    token = os.getenv("NGROK_AUTHTOKEN")
    if not token:
        print(f"{NGROK_BLUE}[Ngrok] Token não encontrado nas variáveis de ambiente!{RESET}")
        exit(1)

    conf.get_default().auth_token = token
    tcp_tunnel = ngrok.connect(addr=MINECRAFT_PORT, proto="tcp")
    url = tcp_tunnel.public_url
    host, port = url.replace("tcp://", "").split(":")

    print(f"\n{BOLD_MINECRAFT_GREEN}[Servidor Online]{RESET}")
    print(f"{BOLD_MINECRAFT_GREEN}ip: {host}:{port}\n{RESET}")
    return host, port

# --- Bot Discord (on_ready para mensagem online inicial) ---
@client.event
async def on_ready():
    # Nick do bot em carmesim/vinho
    print(f"{BOLD_DISCORD_BLUE}[Bot] Logado como {BOLD_CRIMSON_RED}{client.user}{BOLD_DISCORD_BLUE}.{RESET}")
    canal = client.get_channel(CHANNEL_ID)
    if canal is None:
        print(f"{DISCORD_BLUE}[Erro] Canal não encontrado.{RESET}")
        return

    async for msg in canal.history(limit=20):
        if msg.author == client.user:
            await msg.delete()
            print(f"{DISCORD_BLUE}[Bot] Mensagem anterior apagada.{RESET}")
            break

    await canal.send(f"[Servidor Online]\nip: {ip_global}:{port_global}")
    print(f"{BOLD_DISCORD_BLUE}[Bot] Mensagem enviada.{RESET}")
    await asyncio.sleep(5)
    await client.close()
    print(f"{BOLD_DISCORD_BLUE}[Bot] Cliente Discord finalizado.{RESET}")

# --- Iniciar servidor Minecraft ---
def iniciar_server():
    global minecraft_process

    jar_path = os.path.join(SERVER_DIR, SERVER_JAR)
    print(f"{BOLD_MINECRAFT_GREEN}[Minecraft] Tentando rodar o jar: {jar_path}{RESET}")
    if not os.path.isfile(jar_path):
        print(f"{MINECRAFT_GREEN}[Erro] Arquivo server.jar não encontrado no caminho esperado.{RESET}")
        exit(1)

    # Use stdin=subprocess.PIPE e text=True para enviar comandos
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

    print(f"{MINECRAFT_GREEN}[AutoSave] Aguardando {SAVE_INTERVAL_MINUTES} minutos antes do primeiro save...{RESET}")
    await asyncio.sleep(SAVE_INTERVAL_MINUTES * 60)

    while minecraft_process and minecraft_process.poll() is None:
        print(f"{MINECRAFT_GREEN}[AutoSave] Enviando comando /save-all para o servidor...{RESET}")
        try:
            minecraft_process.stdin.write("save-all\n")
            minecraft_process.stdin.flush()
            print(f"{MINECRAFT_GREEN}[AutoSave] Comando /save-all enviado.{RESET}")
        except Exception as e:
            print(f"{MINECRAFT_GREEN}[AutoSave] Erro ao enviar comando /save-all: {e}{RESET}")
            break

        await asyncio.sleep(SAVE_INTERVAL_MINUTES * 60)
    print(f"{MINECRAFT_GREEN}[AutoSave] Tarefa de auto-save finalizada (servidor fechou).{RESET}")

# --- Função Principal ---
async def main():
    global ip_global, port_global, minecraft_process

    usuario = getpass.getuser()
    git_sync()

    host, port = iniciar_ngrok()
    ip_global = host
    port_global = port

    print(f"{BOLD_DISCORD_BLUE}[Bot] Iniciando cliente Discord...{RESET}")
    await client.start(TOKEN)

    print(f"{BOLD_MINECRAFT_GREEN}[Minecraft] Iniciando servidor...{RESET}")
    minecraft_process = iniciar_server()

    auto_save_task_handle = asyncio.create_task(auto_save_task())

    await asyncio.to_thread(minecraft_process.wait)

    print(f"{BOLD_MINECRAFT_GREEN}[Minecraft] Servidor Minecraft fechado.{RESET}")

    if not auto_save_task_handle.done():
        auto_save_task_handle.cancel()
        try:
            await auto_save_task_handle
        except asyncio.CancelledError:
            print(f"{MINECRAFT_GREEN}[AutoSave] Tarefa de auto-save cancelada.{RESET}")

    git_push(usuario)

if __name__ == "__main__":
    # Habilitar suporte a cores ANSI no Windows
    if os.name == 'nt':
        os.system('color') # Isso ativa o processamento de sequências ANSI

    asyncio.run(main())