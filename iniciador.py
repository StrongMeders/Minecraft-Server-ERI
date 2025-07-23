import os
import getpass
import subprocess
from pyngrok import ngrok, conf
from dotenv import load_dotenv
import time
from datetime import datetime


import discord
import asyncio

# Carrega as variáveis do .env
load_dotenv()   

# CONFIGURAÇÕES
SERVER_DIR = os.path.join(os.getcwd(), "server")
SERVER_JAR = "server.jar"
MINECRAFT_PORT = 25565

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# --- Adicione estas linhas para depuração ---
print(f"TOKEN lido: {TOKEN}")
print(f"CHANNEL_ID lido: {CHANNEL_ID}")

# Variáveis globais para o IP e Porta do Ngrok
ip_global = None
port_global = None

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)


def git_sync():
    print("[Git] Sincronizando repositório com origin/main...")
    result_fetch = subprocess.run("git fetch origin", shell=True, cwd=os.getcwd())
    if result_fetch.returncode != 0:
        print("[Git] Erro ao fazer fetch!")
        exit(1)

    result_reset = subprocess.run("git reset --hard origin/main", shell=True, cwd=os.getcwd())
    if result_reset.returncode != 0:
        print("[Git] Erro ao fazer reset!")
        exit(1)
    print("[Git] Repositório sincronizado com sucesso!")

# Iniciar Ngrok
def iniciar_ngrok():
    print("[Ngrok] Iniciando túnel TCP via pyngrok...")

    token = os.getenv("NGROK_AUTHTOKEN")
    if not token:
        print("[Ngrok] Token não encontrado nas variáveis de ambiente!")
        exit(1)

    # Certifica-se de que o token de autenticação está configurado para pyngrok
    conf.get_default().auth_token = token
    tcp_tunnel = ngrok.connect(addr=MINECRAFT_PORT, proto="tcp")

    url = tcp_tunnel.public_url
    host, port = url.replace("tcp://", "").split(":")

    print("\n[Servidor Online]")
    print(f"ip: {host}:{port}\n")

    return host, port

# Bot Discord
@client.event
async def on_ready():
    print(f"[Bot] Logado como {client.user}")

    canal = client.get_channel(CHANNEL_ID)
    if canal is None:
        print("[Erro] Canal não encontrado.")
        await client.close()
        return

    # Apaga última mensagem enviada pelo bot no canal, se houver
    async for msg in canal.history(limit=20):
        if msg.author == client.user:
            await msg.delete()
            print("[Bot] Mensagem anterior apagada.")
            break

    # Envia a nova mensagem com IP e porta atuais
    await canal.send(f"[Servidor Online]\nip: {ip_global}:{port_global}")

    await asyncio.sleep(5)  # espera garantir envio
    await client.close()
    print("[Bot] Mensagem enviada e bot finalizado.")


# Iniciar servidor
def iniciar_server():
    jar_path = os.path.join(SERVER_DIR, SERVER_JAR)
    print(f"[Minecraft] Tentando rodar o jar: {jar_path}")
    if not os.path.isfile(jar_path):
        print("[Erro] Arquivo server.jar não encontrado no caminho esperado.")
        exit(1)
    
    # Use 'java -Xmx1024M -Xms1024M -jar "{jar_path}" nogui' para alocar memória
    # Adapte -Xmx e -Xms conforme a memória que você quer alocar para o servidor.
    processo = subprocess.Popen(f'java -jar "{jar_path}" nogui', cwd=SERVER_DIR, shell=True)
    return processo

def git_push(usuario):
    print("[Git] Fazendo commit e push do backup...")
    datahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    msg_commit = f"{datahora}-{usuario}"
    subprocess.run("git add .", shell=True, cwd=os.getcwd())
    subprocess.run(f'git commit -m "{msg_commit}"', shell=True, cwd=os.getcwd())
    subprocess.run("git push", shell=True, cwd=os.getcwd())
    print("[Git] Backup enviado!")

async def main():
    global ip_global, port_global # Declara que você vai usar as variáveis globais

    usuario = getpass.getuser()
    git_sync()
    # Inicia o Ngrok e obtém o host e a porta
    host, port = iniciar_ngrok()
    ip_global = host
    port_global = port

    # Inicia o cliente Discord para enviar a mensagem
    # O bot irá fechar após enviar a mensagem, conforme configurado em on_ready
    print("[Bot] Iniciando cliente Discord...")
    await client.start(TOKEN) 

    # Inicia o servidor Minecraft
    processo = iniciar_server()
    processo.wait() # Espera o servidor Minecraft terminar
    git_push(usuario)

if __name__ == "__main__":
    asyncio.run(main())