import subprocess
import requests
import time
import os
from datetime import datetime
import getpass

# CONFIGURAÇÕES - ajuste conforme seu ambiente
NGROK_PATH = "ngrok.exe"   # ou caminho absoluto do ngrok
SERVER_DIR = os.path.join(os.getcwd(), "server")
SERVER_JAR = "server.jar"
DISCORD_WEBHOOK = open("webhook.txt").read().strip()  # webhook salvo no arquivo
MINECRAFT_PORT = 25565

def git_pull():
    print("[Git] Fazendo pull do repositório...")
    result = subprocess.run("git pull", shell=True, cwd=os.getcwd())
    if result.returncode != 0:
        print("[Git] Erro ao fazer pull!")
        exit(1)

def iniciar_ngrok():
    print("[Ngrok] Iniciando túnel TCP...")
    # Inicia ngrok em background
    subprocess.Popen(f"{NGROK_PATH} tcp {MINECRAFT_PORT}", shell=True)
    time.sleep(5)  # espera ngrok subir

def pegar_url_ngrok():
    try:
        resp = requests.get("http://localhost:4040/api/tunnels")
        data = resp.json()
        for tunnel in data.get("tunnels", []):
            if tunnel.get("proto") == "tcp":
                return tunnel.get("public_url")
    except Exception as e:
        print(f"[Erro] Falha ao pegar URL ngrok: {e}")
    return None

def enviar_discord(url):
    if not url:
        print("[Discord] URL ngrok não disponível, não enviaremos notificação.")
        return
    msg = {"content": f"🟢 Servidor Minecraft iniciado! IP: `{url}`"}
    resp = requests.post(DISCORD_WEBHOOK, json=msg)
    if resp.status_code == 204:
        print("[Discord] Notificação enviada com sucesso!")
    else:
        print(f"[Discord] Falha ao enviar notificação: {resp.status_code} - {resp.text}")

def iniciar_minecraft():
    print("[Minecraft] Iniciando servidor Minecraft...")
    jar_path = os.path.join(SERVER_DIR, SERVER_JAR)
    processo = subprocess.Popen(f"java -jar {jar_path} nogui", cwd=SERVER_DIR, shell=True)
    return processo

def git_push(usuario):
    print("[Git] Fazendo commit e push do backup...")
    datahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    msg_commit = f"{datahora}-{usuario}"
    # git add . && git commit -m "msg" && git push
    subprocess.run("git add .", shell=True, cwd=os.getcwd())
    subprocess.run(f'git commit -m "{msg_commit}"', shell=True, cwd=os.getcwd())
    subprocess.run("git push", shell=True, cwd=os.getcwd())
    print("[Git] Backup enviado!")

def main():
    usuario = getpass.getuser()
    git_pull()
    iniciar_ngrok()
    time.sleep(5)  # garante túnel ativo
    url = pegar_url_ngrok()
    enviar_discord(url)
    processo = iniciar_minecraft()
    processo.wait()  # aguarda servidor fechar
    git_push(usuario)

if __name__ == "__main__":
    main()
