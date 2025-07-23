import os
import getpass
import subprocess
from pyngrok import ngrok, conf
from dotenv import load_dotenv, find_dotenv # Importe find_dotenv
import asyncio
import discord
from datetime import datetime

# Carrega as variáveis do .env
load_dotenv(override=True, dotenv_path=find_dotenv()) # Adicione override=True aqui para garantir

# CONFIGURAÇÕES
SERVER_DIR = os.path.join(os.getcwd(), "server")
SERVER_JAR = "server.jar"
MINECRAFT_PORT = 25565
SAVE_INTERVAL_MINUTES = 15 # Novo: Intervalo para salvar em minutos

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# --- Adicione estas linhas para depuração ---
print(f"TOKEN lido: {TOKEN}")
print(f"CHANNEL_ID lido: {CHANNEL_ID}")

# Variáveis globais para o IP e Porta do Ngrok
ip_global = None
port_global = None

# Cliente Discord global (o mesmo usado para a mensagem online inicial)
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Processo do servidor Minecraft global para que outras funções possam acessá-lo
minecraft_process = None

# --- Funções Git ---
def git_sync():
    print("[Git] Sincronizando repositório com origin/main...")
    try:
        subprocess.run("git fetch origin", shell=True, cwd=os.getcwd(), check=True)
        subprocess.run("git reset --hard origin/main", shell=True, cwd=os.getcwd(), check=True)
        print("[Git] Repositório sincronizado com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"[Git] Erro ao sincronizar: {e}")
        # Decida se quer sair ou apenas avisar
        exit(1)

def git_push(usuario):
    print("[Git] Fazendo commit e push do backup...")
    datahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    msg_commit = f"{datahora}-{usuario}"
    try:
        subprocess.run("git add .", shell=True, cwd=os.getcwd(), check=True)
        subprocess.run(f'git commit -m "{msg_commit}"', shell=True, cwd=os.getcwd(), check=True)
        subprocess.run("git push", shell=True, cwd=os.getcwd(), check=True)
        print("[Git] Backup enviado!")
    except subprocess.CalledProcessError as e:
        print(f"[Git] Erro ao fazer commit/push: {e}")
    except Exception as e:
        print(f"[Git] Erro inesperado no Git Push: {e}")

# --- Iniciar Ngrok ---
def iniciar_ngrok():
    print("[Ngrok] Iniciando túnel TCP via pyngrok...")
    token = os.getenv("NGROK_AUTHTOKEN")
    if not token:
        print("[Ngrok] Token não encontrado nas variáveis de ambiente!")
        exit(1)

    conf.get_default().auth_token = token
    tcp_tunnel = ngrok.connect(addr=MINECRAFT_PORT, proto="tcp")
    url = tcp_tunnel.public_url
    host, port = url.replace("tcp://", "").split(":")

    print("\n[Servidor Online]")
    print(f"ip: {host}:{port}\n")
    return host, port

# --- Bot Discord (on_ready para mensagem online inicial) ---
@client.event
async def on_ready():
    print(f"[Bot] Logado como {client.user}")
    canal = client.get_channel(CHANNEL_ID)
    if canal is None:
        print("[Erro] Canal não encontrado.")
        # Não fechar o cliente aqui, ele será fechado após o envio.
        return

    async for msg in canal.history(limit=20):
        if msg.author == client.user:
            await msg.delete()
            print("[Bot] Mensagem anterior apagada.")
            break

    await canal.send(f"[Servidor Online]\nip: {ip_global}:{port_global}")
    print("[Bot] Mensagem enviada.")
    await asyncio.sleep(5) # Pequena pausa para garantir o envio
    await client.close() # Fecha o cliente Discord após a mensagem inicial
    print("[Bot] Cliente Discord finalizado.")

# --- Iniciar servidor Minecraft (agora sem wait()) ---
def iniciar_server():
    global minecraft_process # Declara que vai usar a variável global

    jar_path = os.path.join(SERVER_DIR, SERVER_JAR)
    print(f"[Minecraft] Tentando rodar o jar: {jar_path}")
    if not os.path.isfile(jar_path):
        print("[Erro] Arquivo server.jar não encontrado no caminho esperado.")
        exit(1)

    # Use stdin=subprocess.PIPE para poder enviar comandos ao servidor
    # Use text=True para enviar comandos como strings
    minecraft_process = subprocess.Popen(
        f'java -jar "{jar_path}" nogui',
        cwd=SERVER_DIR,
        shell=True,
        stdin=subprocess.PIPE, # Essencial para enviar comandos
        text=True # Para enviar strings
    )
    return minecraft_process

# --- Nova Função: Auto-Save ---
async def auto_save_task():
    global minecraft_process

    # Espera um tempo inicial para o servidor carregar completamente
    print(f"[AutoSave] Aguardando {SAVE_INTERVAL_MINUTES} minutos antes do primeiro save...")
    await asyncio.sleep(SAVE_INTERVAL_MINUTES * 60)

    while minecraft_process and minecraft_process.poll() is None: # Continua enquanto o processo do Minecraft estiver rodando
        print("[AutoSave] Enviando comando /save-all para o servidor...")
        try:
            # Envia o comando para o stdin do processo do servidor.
            # Adicione '\n' para simular um Enter.
            minecraft_process.stdin.write("save-all\n")
            minecraft_process.stdin.flush() # Garante que o comando seja enviado imediatamente
            print("[AutoSave] Comando /save-all enviado.")
        except Exception as e:
            print(f"[AutoSave] Erro ao enviar comando /save-all: {e}")
            break # Sai do loop se não conseguir enviar (ex: pipe fechado)

        # Espera o próximo intervalo
        await asyncio.sleep(SAVE_INTERVAL_MINUTES * 60)
    print("[AutoSave] Tarefa de auto-save finalizada (servidor fechou).")


# --- Função Principal ---
async def main():
    global ip_global, port_global, minecraft_process

    usuario = getpass.getuser()
    git_sync()

    # Inicia o Ngrok e obtém o host e a porta
    host, port = iniciar_ngrok()
    ip_global = host
    port_global = port

    # Inicia o cliente Discord para enviar a mensagem (roda on_ready)
    print("[Bot] Iniciando cliente Discord...")
    # O client.start() vai rodar o on_ready e fechar o cliente automaticamente.
    # Não precisa de try/except aqui diretamente, pois o on_ready já gerencia o envio e close.
    # Apenas certifique-se que o TOKEN está OK.
    await client.start(TOKEN)

    # Inicia o servidor Minecraft (agora não bloqueia)
    print("[Minecraft] Iniciando servidor...")
    minecraft_process = iniciar_server()

    # Cria e inicia a tarefa de auto-save em paralelo
    auto_save_task_handle = asyncio.create_task(auto_save_task())

    # Espera até que o processo do Minecraft termine (o usuário fecha o servidor, etc.)
    # Isso vai bloquear o main até que o servidor seja desligado.
    await asyncio.to_thread(minecraft_process.wait) # Executa .wait() em um thread separado para não bloquear o loop de asyncio

    print("[Minecraft] Servidor Minecraft fechado.")

    # Cancela a tarefa de auto-save, caso ainda esteja rodando
    if not auto_save_task_handle.done():
        auto_save_task_handle.cancel()
        try:
            await auto_save_task_handle # Aguarda o cancelamento
        except asyncio.CancelledError:
            print("[AutoSave] Tarefa de auto-save cancelada.")

    # Faz o backup Git após o servidor fechar
    git_push(usuario)

if __name__ == "__main__":
    asyncio.run(main())