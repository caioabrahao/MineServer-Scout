import socket
import struct
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm   # barra de progresso
import sys

# ---- Função para pegar status Minecraft ----
def get_mc_status(host, port, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        # Handshake packet
        host_bytes = host.encode("utf-8")
        data = (
            b"\x00"  # packet id = 0 (handshake)
            + b"\x00"  # protocol version (handshake mode)
            + struct.pack("!B", len(host_bytes)) + host_bytes  # host
            + struct.pack("!H", port)  # port
            + b"\x01"  # next state = status
        )
        packet = struct.pack("!B", len(data)) + data
        sock.sendall(packet)

        # Send request packet
        sock.sendall(b"\x01\x00")

        # Read response length
        length = read_varint(sock)
        packet_id = read_varint(sock)
        if packet_id != 0x00:
            return None

        # Read JSON response
        response_length = read_varint(sock)
        data = b""
        while len(data) < response_length:
            chunk = sock.recv(response_length - len(data))
            if not chunk:
                break
            data += chunk

        sock.close()
        response = json.loads(data.decode("utf-8"))
        return response
    except Exception:
        return None

# ---- Função auxiliar para varint ----
def read_varint(sock):
    i = 0
    j = 0
    while True:
        byte = sock.recv(1)
        if not byte:
            return 0
        byte = ord(byte)
        i |= (byte & 0x7F) << 7 * j
        j += 1
        if not (byte & 0x80):
            break
    return i

# ---- Função para testar uma porta ----
def test_port(host, port, timeout=1):
    status = get_mc_status(host, port, timeout)
    if status:
        motd = status["description"]["text"] if isinstance(status["description"], dict) else status["description"]
        version = status["version"]["name"]
        players = f'{status["players"]["online"]}/{status["players"]["max"]}'
        return port, version, motd, players
    return None

# ---- Main ----
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python scan_ports.py <host> <porta_inicial> <porta_final>")
        sys.exit(1)

    host = sys.argv[1]
    start_port = int(sys.argv[2])
    end_port = int(sys.argv[3])

    results = []

    print(f"🔎 Iniciando varredura em {host} ({start_port}-{end_port})...\n")

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(test_port, host, port) for port in range(start_port, end_port + 1)]

        for f in tqdm(as_completed(futures), total=len(futures), desc="Progresso"):
            result = f.result()
            if result:
                results.append(result)

    print("\n--- Resultados ---")
    if results:
        for port, version, motd, players in results:
            print(f"[{port}] ✅ {version} | MOTD: \"{motd}\" | Players: {players}")
    else:
        print("Nenhum servidor Minecraft encontrado.")
