import subprocess
import requests
import time
import os
from datetime import datetime
import getpass
import sys

# Descobre o diretório do script atual (mesmo dentro do .exe com PyInstaller)
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

# CONFIGURAÇÕES
NGROK_PATH = os.path.join(BASE_DIR, "ngrok.exe")
SERVER_DIR = os.path.join(BASE_DIR, "server")
SERVER_JAR = "server.jar"
WEBHOOK_PATH = os.path.join(BASE_DIR, "webhook.txt")
MINECRAFT_PORT = 25565

# # Lê o webhook
# if not os.path.exists(WEBHOOK_PATH):
#     print(f"[Erro] Arquivo webhook.txt não encontrado em: {WEBHOOK_PATH}")
#     input("Pressione Enter para sair...")
#     exit(1)

# with open(WEBHOOK_PATH, "r") as f:
#     DISCORD_WEBHOOK = f.read().strip()

def git_pull():
    print("[Git] Fazendo pull do repositório...")
    result = subprocess.run("git pull", shell=True, cwd=BASE_DIR)
    if result.returncode != 0:
        print("[Git] Erro ao fazer pull!")
        exit(1)

# def iniciar_ngrok():
#     print("[Ngrok] Iniciando túnel TCP...")
#     subprocess.Popen(f"{NGROK_PATH} tcp {MINECRAFT_PORT}", shell=True)
#     time.sleep(5)

# def pegar_url_ngrok():
#     try:
#         resp = requests.get("http://localhost:4040/api/tunnels")
#         data = resp.json()
#         for tunnel in data.get("tunnels", []):
#             if tunnel.get("proto") == "tcp":
#                 return tunnel.get("public_url")
#     except Exception as e:
#         print(f"[Erro] Falha ao pegar URL ngrok: {e}")
#     return None

# def enviar_discord(url):
#     if not url:
#         print("[Discord] URL ngrok não disponível, não enviaremos notificação.")
#         return
#     msg = {"content": f"🟢 Servidor Minecraft iniciado! IP: `{url}`"}
#     resp = requests.post(DISCORD_WEBHOOK, json=msg)
#     if resp.status_code == 204:
#         print("[Discord] Notificação enviada com sucesso!")
#     else:
#         print(f"[Discord] Falha ao enviar notificação: {resp.status_code} - {resp.text}")

def iniciar_minecraft():
    print("[Minecraft] Iniciando servidor Minecraft...")
    jar_path = os.path.join(SERVER_DIR, SERVER_JAR)
    print(f"Executando jar: {jar_path}")
    processo = subprocess.Popen(
        ["java", "-jar", jar_path, "nogui"],
        cwd=SERVER_DIR
    )
    return processo


def git_push(usuario):
    print("[Git] Fazendo commit e push do backup...")
    datahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    msg_commit = f"{datahora}-{usuario}"
    subprocess.run("git add .", shell=True, cwd=BASE_DIR)
    subprocess.run(f'git commit -m "{msg_commit}"', shell=True, cwd=BASE_DIR)
    subprocess.run("git push", shell=True, cwd=BASE_DIR)
    print("[Git] Backup enviado!")

def main():
    usuario = getpass.getuser()
    git_pull()
    # iniciar_ngrok()
    # time.sleep(5)
    # url = pegar_url_ngrok()
    # enviar_discord(url)
    processo = iniciar_minecraft()
    processo.wait()
    git_push(usuario)

if __name__ == "__main__":
    main()
