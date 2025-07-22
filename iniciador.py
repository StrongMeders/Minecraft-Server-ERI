import subprocess
import time
import os
from datetime import datetime
import getpass
from pyngrok import ngrok

# CONFIGURAÇÕES
SERVER_DIR = os.path.join(os.getcwd(), "server")
SERVER_JAR = "server.jar"
MINECRAFT_PORT = 25565

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


# def iniciar_ngrok():
#     print("[Ngrok] Iniciando túnel TCP via pyngrok...")
#     tcp_tunnel = ngrok.connect(addr=MINECRAFT_PORT, proto="tcp")
#     print(f"[Ngrok] Endereço: {tcp_tunnel.public_url}")
#     return tcp_tunnel.public_url

def iniciar_server():
    jar_path = os.path.join(SERVER_DIR, SERVER_JAR)
    print(f"[Minecraft] Tentando rodar o jar: {jar_path}")
    if not os.path.isfile(jar_path):
        print("[Erro] Arquivo server.jar não encontrado no caminho esperado.")
        exit(1)
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

def main():
    usuario = getpass.getuser()
    git_pull()
    # iniciar_ngrok()
    processo = iniciar_server()
    processo.wait()
    git_push(usuario)

if __name__ == "__main__":
    main()