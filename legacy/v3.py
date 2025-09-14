import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket, struct, json
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---- Handshake/status do Minecraft ----
def read_varint(sock):
    i, j = 0, 0
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

def get_mc_status(host, port, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        host_bytes = host.encode("utf-8")
        data = (
            b"\x00"
            + b"\x00"
            + struct.pack("!B", len(host_bytes)) + host_bytes
            + struct.pack("!H", port)
            + b"\x01"
        )
        packet = struct.pack("!B", len(data)) + data
        sock.sendall(packet)
        sock.sendall(b"\x01\x00")

        _ = read_varint(sock)  # packet length
        packet_id = read_varint(sock)
        if packet_id != 0x00:
            return None

        response_length = read_varint(sock)
        data = b""
        while len(data) < response_length:
            chunk = sock.recv(response_length - len(data))
            if not chunk:
                break
            data += chunk

        sock.close()
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None

# ---- Testa porta ----
def test_port(host, port):
    status = get_mc_status(host, port)
    if status:
        motd = status["description"]["text"] if isinstance(status["description"], dict) else status["description"]
        version = status["version"]["name"]
        players = f'{status["players"]["online"]}/{status["players"]["max"]}'
        mods = []
        if "modinfo" in status:
            mods = [m["modid"] + "@" + m["version"] for m in status["modinfo"].get("modList", [])]
        return port, version, motd, players, mods
    return None

# ---- Função principal para varredura ----
def scan():
    host = entry_host.get()
    try:
        start_port = int(entry_start.get())
        end_port = int(entry_end.get())
    except ValueError:
        messagebox.showerror("Erro", "Portas inválidas!")
        return

    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, f"🔎 Escaneando {host} ({start_port}-{end_port})...\n")

    results = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(test_port, host, port) for port in range(start_port, end_port + 1)]
        for f in as_completed(futures):
            result = f.result()
            if result:
                results.append(result)
                port, version, motd, players, mods = result
                text_area.insert(tk.END, f"[{port}] ✅ {version} | {players} | MOTD: \"{motd}\"\n")
                if mods:
                    text_area.insert(tk.END, f"    Mods: {', '.join(mods)}\n")

    if not results:
        text_area.insert(tk.END, "\nNenhum servidor encontrado.\n")

# ---- Interface Tkinter ----
root = tk.Tk()
root.title("Minecraft Server Scanner")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Host:").grid(row=0, column=0, sticky="e")
entry_host = tk.Entry(frame, width=25)
entry_host.grid(row=0, column=1, padx=5)

tk.Label(frame, text="Porta inicial:").grid(row=1, column=0, sticky="e")
entry_start = tk.Entry(frame, width=10)
entry_start.grid(row=1, column=1, sticky="w")

tk.Label(frame, text="Porta final:").grid(row=2, column=0, sticky="e")
entry_end = tk.Entry(frame, width=10)
entry_end.grid(row=2, column=1, sticky="w")

btn = tk.Button(frame, text="Scan", command=scan)
btn.grid(row=3, columnspan=2, pady=5)

text_area = scrolledtext.ScrolledText(root, width=70, height=20)
text_area.pack(pady=10)

root.mainloop()
