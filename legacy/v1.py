import socket
import time

host = "enx-cirion-18.enx.host"  # IP
start_port = 10000
end_port = 10100  # portas

valid_ports = []

print(f"Iniciando varredura em {host} de {start_port} até {end_port}...\n")

for port in range(start_port, end_port + 1):
    print(f"🔎 Testando porta {port}...", end=" ")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)  # timeout de 1 segundo
    try:
        s.connect((host, port))
        print("✅ Porta aberta!")
        valid_ports.append(port)
    except (socket.timeout, ConnectionRefusedError, OSError):
        print("❌ Fechada")
    finally:
        s.close()
    time.sleep(0.05)  # pequeno delay pra não congestionar

print("\n--- Varredura concluída ---")
print("Portas válidas encontradas:", valid_ports if valid_ports else "Nenhuma")
