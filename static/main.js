let table = $('#results').DataTable({
    columnDefs: [
        {
            targets: 0, // Favicon column
            orderable: false,
            searchable: false,
            render: function(data, type, row, meta) {
                // Always render as HTML
                return data;
            }
        }
    ],
    createdRow: function(row, data, dataIndex) {
        // No-op, but can be used for further customization
    }
});

let eventSource = null;
let totalPorts = 0;
let foundServers = 0;

function startScan(){
    table.clear().draw();
    foundServers = 0;
    let host = $("#host").val();
    let start_port = $("#start_port").val();
    let end_port = $("#end_port").val();
    $("#scan_btn").prop("disabled", true).text("Escaneando...");
    if (eventSource) { eventSource.close(); }
    $("#status").html(`
        <span class="flex items-center justify-center gap-2 text-blue-600">
            <svg class="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
            </svg>
            Iniciando varredura...
        </span>
    `).css("color", "");
    $("#progress_container").show();
    $("#progress_bar").css("width", "0%");
    $("#progress_text").text("0%");
    startRealtimeScan(host, start_port, end_port);
}

function startRealtimeScan(host, start_port, end_port) {
    fetch('/scan_realtime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({host, start_port, end_port})
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        function readStream() {
            return reader.read().then(({ done, value }) => {
                if (done) return;
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            handleRealtimeEvent(data, host);
                        } catch (e) { console.error('Error parsing SSE data:', e); }
                    }
                }
                return readStream();
            });
        }
        return readStream();
    })
    .catch(error => {
        console.error('Error during real-time scan:', error);
        $("#status").html(`<span class='text-red-600'>❌ Ocorreu um erro durante o scan.</span>`);
        $("#progress_container").hide();
        $("#scan_btn").prop("disabled", false).text("Scan");
    });
}

function handleRealtimeEvent(data, host) {
    switch(data.type) {
        case 'status':
            $("#status").html(`
                <span class="flex items-center justify-center gap-2 text-blue-600">
                    <svg class="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                    </svg>
                    ${data.message}
                </span>
            `);
            totalPorts = data.total_ports;
            break;
        case 'result':
            foundServers++;
            addServerToTable(data.data, host);
            break;
        case 'progress':
            const percentage = Math.round((data.completed / data.total) * 100);
            $("#progress_bar").css("width", percentage + "%");
            $("#progress_text").text(`${data.completed}/${data.total} portas (${percentage}%)`);
            break;
        case 'complete':
            $("#progress_container").hide();
            $("#scan_btn").prop("disabled", false).text("Scan");
            if (foundServers === 0) {
                $("#status").html(`<span class='text-red-600'>❌ Nenhum servidor encontrado neste range.</span>`);
            } else {
                $("#status").html(`<span class='text-green-600'>✅ Scan concluído! ${foundServers} servidor(es) encontrado(s).</span>`);
            }
            break;
    }
}

function addServerToTable(server, host) {
    const ipButton = `<input type="text" value="${host}:${server.port}" id="ip_${server.port}" readonly class="px-2 py-1 rounded border border-gray-300 w-28 text-xs mr-2">\n                      <button class="bg-blue-600 hover:bg-blue-700 text-white rounded px-2 py-1 text-xs copy-btn" onclick="copyToClipboard('ip_${server.port}')">Copiar</button>`;
    const favicon = createFaviconElement(server.favicon);
    table.row.add([
        favicon,
        server.port,
        server.version,
        server.motd,
        server.players,
        ipButton
    ]).draw(false);
}

function createFaviconElement(faviconData) {
    if (!faviconData) {
        return `<div class="w-8 h-8 bg-gray-300 rounded favicon-placeholder">?</div>`;
    }
    let cleanFaviconData = faviconData;
    if (faviconData.startsWith('data:image/png;base64,')) {
        cleanFaviconData = faviconData.replace('data:image/png;base64,', '');
    }
    return `<div class="relative">
        <img src="data:image/png;base64,${cleanFaviconData}" 
             class="w-8 h-8 rounded favicon" 
             alt="Server Icon" 
             onerror="handleFaviconError(this)"
             onload="handleFaviconLoad(this)"
             style="display: none;">
        <div class="w-8 h-8 bg-gray-300 rounded favicon-placeholder" 
             style="position: absolute; top: 0; left: 0;">⏳</div>
    </div>`;
}

function handleFaviconError(img) {
    img.style.display = 'none';
    const placeholder = img.nextElementSibling;
    if (placeholder) {
        placeholder.textContent = '?';
        placeholder.style.display = 'flex';
    }
}

function handleFaviconLoad(img) {
    img.style.display = 'block';
    const placeholder = img.nextElementSibling;
    if (placeholder) {
        placeholder.style.display = 'none';
    }
}

function copyToClipboard(elementId) {
    const copyText = document.getElementById(elementId);
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    document.execCommand("copy");
    alert(`Copiado: ${copyText.value}`);
}
