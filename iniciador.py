import os
import subprocess
import datetime
import time
import requests

# CONFIGURAÇÕES
NGROK_AUTH_TOKEN = "SEU_TOKEN_AQUI"
NGROK_REGION = "us"
GITHUB_USERNAME = "seu-usuario"
GITHUB_REPO = "nome-do-repo"
GITHUB_BRANCH = "main"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/SEU_WEBHOOK"

# Função utilitária
def run_cmd(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# 1. Puxar o último backup do GitHub
print("🔄 Fazendo pull do backup...")
run_cmd(["git", "pull", "origin", GITHUB_BRANCH])

# 2. Iniciar o servidor do Minecraft (modifique o nome do .jar conforme o seu)
print("🚀 Iniciando servidor...")
server_process = subprocess.Popen(["java", "-Xmx4G", "-Xms2G", "-jar", "server.jar", "nogui"])

# 3. Esperar alguns segundos antes de subir o ngrok
time.sleep(10)

# 4. Subir o ngrok (porta 25565)
print("🌐 Abrindo túnel com ngrok...")
run_cmd(["ngrok", "config", "add-authtoken", NGROK_AUTH_TOKEN])
ngrok_process = subprocess.Popen(["ngrok", "tcp", "25565", "--region", NGROK_REGION], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 5. Esperar o ngrok inicializar e obter o endereço
print("⏳ Aguardando ngrok iniciar...")
time.sleep(8)
try:
    ngrok_data = requests.get("http://localhost:4040/api/tunnels").json()
    public_url = ngrok_data['tunnels'][0]['public_url'].replace("tcp://", "")
except Exception as e:
    public_url = "Erro ao obter porta"
    print(f"⚠️ Erro ao buscar túnel ngrok: {e}")

# 6. Enviar IP para Discord
msg = {
    "content": f"🎮 Servidor Minecraft iniciado!\nEndereço: `{public_url}`"
}
requests.post(DISCORD_WEBHOOK_URL, json=msg)

# 7. Aguardar processo de servidor terminar
print("🕹️ Aguardando o servidor encerrar...")
server_process.wait()

# 8. Após encerrar, salvar e enviar para o GitHub
print("💾 Salvando e fazendo push...")
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
run_cmd(["git", "add", "."])
run_cmd(["git", "commit", "-m", f"{timestamp}-I am the ALL RANGE"])
run_cmd(["git", "push", "origin", GITHUB_BRANCH])

print("✅ Tudo finalizado com sucesso!")
