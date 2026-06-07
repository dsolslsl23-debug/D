import json
import os
import http.server
import socketserver
from http.server import SimpleHTTPRequestHandler

# HTML файл с картой, ИСПРАВЛЕННЫМИ контролами и окном приветствия
MAP_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Карта событий</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body { 
            margin: 0; 
            padding: 0; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }
        
        /* Карта занимает ВСЮ доступную область */
        #map { 
            height: 100vh; 
            width: 100%; 
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
        }
        
        /* Общие стили для всех контролов */
        .controls, .markers-list {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            font-size: 14px;
            z-index: 1000 !important; /* ВЫШЕ карты */
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        /* ПАНЕЛЬ СПИСКА (Слева) */
        .markers-list {
            position: absolute;
            top: 20px;
            left: 20px;
            width: 260px;
            max-height: 80vh;
            overflow-y: auto;
            transition: transform 0.3s ease;
        }
        
        /* ПАНЕЛЬ ДОБАВЛЕНИЯ (Справа) */
        .controls {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 260px;
        }
        
        /* Адаптация под планшеты и телефоны */
        @media (max-width: 768px) {
            .markers-list {
                top: auto;
                bottom: 20px;
                left: 20px;
                right: 20px;
                width: auto;
                max-height: 35vh;
                font-size: 14px;
            }
            
            .controls {
                top: 20px;
                right: 20px;
                left: auto;
                width: 220px;
                font-size: 13px;
            }
            
            .controls h4 { font-size: 14px; margin: 0 0 5px 0; }
            .controls input, .controls button { padding: 8px; margin: 4px 0; }
            .marker-item { padding: 8px; }
        }
        
        /* Для очень маленьких телефонов */
        @media (max-width: 480px) {
            .controls { width: 180px; padding: 8px; top: 10px; right: 10px; }
            .markers-list { padding: 8px; bottom: 10px; left: 10px; right: 10px; }
            .controls input, .controls button { font-size: 12px; }
        }
        
        /* Стили элементов списка */
        .marker-item {
            padding: 8px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }
        .marker-item:hover {
            background: #f5f5f5;
        }
        
        button {
            background: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 8px;
            font-weight: 500;
        }
        button:hover {
            background: #45a049;
        }
        .delete-btn {
            background: #ff4444;
            padding: 4px 8px;
            border-radius: 8px;
            font-size: 12px;
        }
        .delete-btn:hover {
            background: #cc0000;
        }

        /* Стили для модального окна приветствия (без изменений) */
        .welcome-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(8px);
            z-index: 2000;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: Arial, sans-serif;
            transition: opacity 0.3s ease;
        }
        .welcome-content {
            background: white;
            border-radius: 32px;
            padding: 30px 25px;
            text-align: center;
            max-width: 340px;
            width: 85%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            animation: slideIn 0.4s cubic-bezier(0.34, 1.2, 0.64, 1);
        }
        @keyframes slideIn {
            from {
                transform: scale(0.9) translateY(20px);
                opacity: 0;
            }
            to {
                transform: scale(1) translateY(0);
                opacity: 1;
            }
        }
        .avatar {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 48px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
        .welcome-content h2 {
            color: #333;
            margin-bottom: 12px;
            font-size: 24px;
        }
        .welcome-content p {
            color: #666;
            line-height: 1.5;
            margin-bottom: 25px;
            font-size: 14px;
        }
        .close-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 28px;
            border: none;
            border-radius: 40px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: auto;
        }
        .close-btn:hover {
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(102,126,234,0.4);
        }
        .tip {
            font-size: 12px;
            color: #aaa;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div id="map"></div>

    <!-- Модальное окно приветствия -->
    <div id="welcomeModal" class="welcome-modal">
        <div class="welcome-content">
            <div class="avatar">🗺️</div>
            <h2>Добро пожаловать!</h2>
            <p>
                📍 Кликните по карте, чтобы добавить метку<br>
                🏷️ Дайте название точке<br>
                🗑️ Удаляйте из списка слева
            </p>
            <button class="close-btn" onclick="closeWelcomeModal()">Начать →</button>
            <div class="tip">💡 Панели управления — слева и справа</div>
        </div>
    </div>

    <!-- Панель добавления (Справа) -->
    <div class="controls">
        <h4 style="margin:0 0 8px 0">➕ Добавить метку</h4>
        <input type="text" id="markerName" placeholder="Название" style="width:100%; padding:8px; border:1px solid #ddd; border-radius:8px; box-sizing:border-box;">
        <button onclick="addMarkerByCoords()" style="width:100%; padding:8px; margin-top:5px;">По координатам</button>
        <small style="display:block; text-align:center; margin-top:6px; color:#666;">Или кликните по карте</small>
    </div>

    <!-- Панель списка (Слева) -->
    <div class="markers-list">
        <h4 style="margin:0 0 8px 0">📌 Список меток</h4>
        <div id="markersList" style="max-height:calc(100% - 70px); overflow-y:auto;"></div>
        <button onclick="clearAllMarkers()" style="background:#ff4444; width:100%; padding:8px; margin-top:10px;">🗑️ Очистить все</button>
    </div>

    <script>
        // Инициализация карты
        var map = L.map('map').setView([55.751244, 37.618423], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        var markers = {};
        var nextId = 0;

        // Функция закрытия окна приветствия
        function closeWelcomeModal() {
            const modal = document.getElementById('welcomeModal');
            modal.style.opacity = '0';
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
        }

        // Загрузка сохраненных меток
        async function loadMarkers() {
            try {
                let response = await fetch('/markers');
                let data = await response.json();
                for (let id in data) {
                    let m = data[id];
                    addMarkerToMap(id, m.lat, m.lng, m.name);
                    if (parseInt(id) >= nextId) nextId = parseInt(id) + 1;
                }
                updateList();
            } catch(e) { console.log(e); }
        }

        function addMarkerToMap(id, lat, lng, name) {
            var marker = L.marker([lat, lng]).addTo(map);
            marker.bindPopup("<b>" + name + "</b><br>" + lat + ", " + lng);
            markers[id] = { marker: marker, lat: lat, lng: lng, name: name };
            updateList();
        }

        function saveMarker(id, lat, lng, name) {
            fetch('/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id, lat: lat, lng: lng, name: name })
            });
        }

        function deleteMarker(id) {
            fetch('/delete?id=' + id);
            if (markers[id]) {
                map.removeLayer(markers[id].marker);
                delete markers[id];
                updateList();
            }
        }

        function updateList() {
            var listDiv = document.getElementById('markersList');
            listDiv.innerHTML = '';
            for (let id in markers) {
                let m = markers[id];
                let div = document.createElement('div');
                div.className = 'marker-item';
                div.innerHTML = '<div><b>' + m.name + '</b><br><small>' + m.lat.toFixed(4) + ', ' + m.lng.toFixed(4) + '</small></div>';
                div.onclick = (function(lat, lng) { 
                    return function() { map.setView([lat, lng], 15); };
                })(m.lat, m.lng);

                let delBtn = document.createElement('button');
                delBtn.innerHTML = '✕';
                delBtn.className = 'delete-btn';
                delBtn.onclick = (function(id) { return function(e) { 
                    e.stopPropagation(); 
                    deleteMarker(id); 
                }; })(id);
                div.appendChild(delBtn);
                listDiv.appendChild(div);
            }
        }

        function addMarker(lat, lng, name) {
            let id = nextId++;
            addMarkerToMap(id, lat, lng, name);
            saveMarker(id, lat, lng, name);
        }

        function addMarkerByCoords() {
            let lat = parseFloat(prompt("Широта:", "55.751244"));
            let lng = parseFloat(prompt("Долгота:", "37.618423"));
            let name = document.getElementById('markerName').value;
            if (!name) name = prompt("Название метки:", "Новое событие");
            if (lat && lng && name) addMarker(lat, lng, name);
            document.getElementById('markerName').value = '';
        }

        function clearAllMarkers() {
            if (confirm("Удалить все метки?")) {
                for (let id in markers) deleteMarker(id);
            }
        }

        map.on('click', function(e) {
            let name = prompt("Название метки:", "Новое событие");
            if (name) addMarker(e.latlng.lat, e.latlng.lng, name);
        });

        loadMarkers();
    </script>
</body>
</html>"""

class MarkerHandler(http.server.SimpleHTTPRequestHandler):
    markers_file = "markers_web.json"

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(MAP_HTML.encode())
        elif self.path == '/markers':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            markers = {}
            if os.path.exists(self.markers_file):
                with open(self.markers_file, 'r') as f:
                    markers = json.load(f)
            self.wfile.write(json.dumps(markers).encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/save':
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length).decode())
            markers = {}
            if os.path.exists(self.markers_file):
                with open(self.markers_file, 'r') as f:
                    markers = json.load(f)
            markers[data['id']] = {'lat': data['lat'], 'lng': data['lng'], 'name': data['name']}
            with open(self.markers_file, 'w') as f:
                json.dump(markers, f, indent=2)
            self.send_response(200)
            self.end_headers()

    def do_DELETE(self):
        if self.path.startswith('/delete'):
            id = self.path.split('=')[1]
            markers = {}
            if os.path.exists(self.markers_file):
                with open(self.markers_file, 'r') as f:
                    markers = json.load(f)
            if id in markers:
                del markers[id]
            with open(self.markers_file, 'w') as f:
                json.dump(markers, f, indent=2)
            self.send_response(200)
            self.end_headers()

    def log_message(self, format, *args):
        pass

# Получаем порт от Railway
PORT = int(os.environ.get("PORT", 8080))

def start_server():
    handler = MarkerHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"🌍 Сервер запущен на порту {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()
