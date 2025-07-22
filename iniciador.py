import subprocess
import time
import os
from pyngrok import ngrok
from datetime import datetime

# Caminhos relativos
PASTA_SERVIDOR = "server"
JAR_NAME = "server.jar"
PORTA_MINECRAFT = 25565

def iniciar_ngrok():
    print("[Ngrok] Iniciando túnel TCP via pyngrok...")
    tunel = ngrok.connect(PORTA_MINECRAFT, "tcp")
    print(f"[Ngrok] Endereço: {tunel.public_url}")
    # (aqui futuramente podemos enviar isso pro Discord)
    return tunel.public_url

def iniciar_minecraft():
    print("[Minecraft] Iniciando servidor Minecraft...")
    caminho_jar = os.path.join(PASTA_SERVIDOR, JAR_NAME)
    subprocess.run(["java", "-Xmx2G", "-Xms2G", "-jar", caminho_jar, "nogui"], cwd=PASTA_SERVIDOR)

def git_pull():
    print("[Git] Fazendo pull do repositório...")
    subprocess.run(["git", "pull"])

def git_push():
    print("[Git] Fazendo commit e push do backup...")
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"{data_hora}_backup"])
    subprocess.run(["git", "push"])
    print("[Git] Backup enviado!")

# Execução principal
git_pull()
url_ngrok = iniciar_ngrok()
iniciar_minecraft()
git_push()
