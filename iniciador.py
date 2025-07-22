import subprocess
import requests
import time
import os
from datetime import datetime

usuario = os.getenv("USERNAME") or "user"
hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

print("🔄 Fazendo pull do backup...")
subprocess.run(["git", "pull"])

print("🚀 Iniciando servidor...")
# Substitua abaixo se o seu .jar tiver outro nome
subprocess.Popen(["java", "-Xmx2G", "-jar", "server.jar"])

print("🌐 Abrindo túnel com ngrok...")
subprocess.Popen(["ngrok", "tcp", "25565"])

print("⏳ Aguardando ngrok iniciar...")
time.sleep(5)

try:
    res = requests.get("http://localhost:4040/api/tunnels").json()
    public_url = res["tunnels"][0]["public_url"]
    print("🔗 Endereço público:", public_url)
except Exception as e:
    print("⚠️ Erro ao buscar túnel ngrok:", e)
    public_url = None

print("🕹️ Aguardando o servidor encerrar...")
input("Pressione ENTER quando quiser encerrar o servidor...")

print("💾 Salvando e fazendo push...")
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", f"{hora}-I am the ALL RANGE"])
subprocess.run(["git", "push"])
print("✅ Tudo finalizado com sucesso!")
