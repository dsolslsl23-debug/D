import json
import os
import http.server
import socketserver
from http.server import SimpleHTTPRequestHandler

# HTML файл с картой и окном приветствия
MAP_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Карта событий</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: Arial; }
        #map { height: 100vh; width: 100%; }
        .controls {
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            max-width: 250px;
        }
        .controls input, .controls button {
            margin: 5px 0;
            padding: 5px;
            width: 100%;
        }
        .markers-list {
            position: absolute;
            top: 10px;
            left: 10px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            z-index: 1000;
            max-height: 300px;
            overflow-y: auto;
            min-width: 200px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .marker-item {
            padding: 5px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }
        .marker-item:hover {
            background: #f0f0f0;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background: #45a049;
        }
        .delete-btn {
            background: #ff4444;
            margin-left: 5px;
        }

        /* Стили для модального окна приветствия */
        .welcome-modal {
            display: flex;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 2000;
            justify-content: center;
            align-items: center;
            font-family: Arial, sans-serif;
        }
        .welcome-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            max-width: 400px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        .avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 60px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        .welcome-content h2 {
            color: #333;
            margin-bottom: 15px;
        }
        .welcome-content p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 25px;
        }
        .close-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .close-btn:hover {
            transform: scale(1.05);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        .tip {
            font-size: 12px;
            color: #999;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div id="map"></div>

    <!-- Модальное окно приветствия -->
    <div id="welcomeModal" class="welcome-modal">
        <div class="welcome-content">
            <div class="avatar">
                🗺️
            </div>
            <h2>Добро пожаловать в Карту Событий!</h2>
            <p>
                ✨ Здесь вы можете отмечать важные места на карте<br><br>
                📍 Кликните по карте, чтобы добавить метку<br>
                🏷️ Дайте название каждой точке<br>
                🗑️ Удаляйте ненужные метки из списка
            </p>
            <button class="close-btn" onclick="closeWelcomeModal()">Начать путешествие →</button>
            <div class="tip">💡 Совет: Попробуйте кликнуть в любом месте карты!</div>
        </div>
    </div>

    <div class="controls">
        <h4>➕ Добавить метку</h4>
        <input type="text" id="markerName" placeholder="Название метки">
        <button onclick="addMarkerByCoords()">Добавить по координатам</button>
        <small>Или кликните по карте</small>
    </div>

    <div class="markers-list">
        <h4>📌 Список меток</h4>
        <div id="markersList"></div>
        <button onclick="clearAllMarkers()" style="background:#ff4444">🗑️ Очистить все</button>
    </div>

    <script>
        var map = L.map('map').setView([55.751244, 37.618423], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        var markers = {};
        var nextId = 0;

        // Функция закрытия окна приветствия
        function closeWelcomeModal() {
            const modal = document.getElementById('welcomeModal');
            modal.style.animation = 'slideIn 0.3s reverse';
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
                div.innerHTML = '<b>' + m.name + '</b><br><small>' + m.lat + ', ' + m.lng + '</small>';
                div.onclick = (function(lat, lng) { 
                    return function() { map.setView([lat, lng], 15); };
                })(m.lat, m.lng);

                let delBtn = document.createElement('button');
                delBtn.innerHTML = '❌';
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
