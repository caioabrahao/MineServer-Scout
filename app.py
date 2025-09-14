from flask import Flask, render_template, request, jsonify
import socket, struct, json
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# ---- Funções para handshake MC ----
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
            b"\x00" + b"\x00"
            + struct.pack("!B", len(host_bytes)) + host_bytes
            + struct.pack("!H", port)
            + b"\x01"
        )
        packet = struct.pack("!B", len(data)) + data
        sock.sendall(packet)
        sock.sendall(b"\x01\x00")

        _ = read_varint(sock)
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

def test_port(host, port):
    status = get_mc_status(host, port)
    if status:
        motd = status["description"]["text"] if isinstance(status["description"], dict) else status["description"]
        version = status["version"]["name"]
        players = f'{status["players"]["online"]}/{status["players"]["max"]}'
        mods = []
        if "modinfo" in status:
            mods = [m["modid"] + "@" + m["version"] for m in status["modinfo"].get("modList", [])]
        return {"port": port, "version": version, "motd": motd, "players": players, "mods": mods}
    return None

# ---- Rotas Flask ----
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    host = data.get("host")
    start_port = int(data.get("start_port"))
    end_port = int(data.get("end_port"))

    results = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(test_port, host, port) for port in range(start_port, end_port + 1)]
        for f in as_completed(futures):
            result = f.result()
            if result:
                results.append(result)
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
