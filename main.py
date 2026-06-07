import json
import os
import http.server
import socketserver
from http.server import SimpleHTTPRequestHandler

# HTML файл с картой и музыкой - УВЕЛИЧЕННЫЙ АВАТАР 250px
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
        
        /* Панель добавления меток (справа вверху) */
        .controls {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 260px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        .controls h4 {
            margin: 0 0 8px 0;
            font-size: 14px;
        }
        
        .controls input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 14px;
        }
        
        .controls button {
            width: 100%;
            padding: 8px;
            margin-top: 5px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .controls button:hover {
            background: #45a049;
        }
        
        .controls small {
            display: block;
            text-align: center;
            margin-top: 6px;
            color: #666;
            font-size: 11px;
        }
        
        /* КНОПКА ВЫЗОВА СПИСКА МЕТОК */
        .show-list-btn {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            z-index: 1000;
            font-size: 16px;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 8px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .show-list-btn:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(102,126,234,0.4);
        }
        
        /* КНОПКА УПРАВЛЕНИЯ МУЗЫКОЙ */
        .music-control {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 40px;
            cursor: pointer;
            z-index: 1000;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
            font-weight: normal;
        }
        
        .music-control:hover {
            background: rgba(0, 0, 0, 0.85);
            transform: scale(1.02);
        }
        
        /* МОДАЛЬНОЕ ОКНО СО СПИСКОМ МЕТОК */
        .markers-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            z-index: 2000;
            justify-content: center;
            align-items: center;
        }
        
        .markers-modal.active {
            display: flex;
        }
        
        .markers-modal-content {
            background: white;
            border-radius: 24px;
            width: 90%;
            max-width: 400px;
            max-height: 70vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            animation: modalSlideIn 0.3s ease-out;
        }
        
        @keyframes modalSlideIn {
            from {
                opacity: 0;
                transform: scale(0.95) translateY(-10px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }
        
        .markers-modal-header {
            padding: 20px 20px 10px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .markers-modal-header h3 {
            margin: 0;
            font-size: 18px;
            color: #333;
        }
        
        .close-modal-btn {
            background: none;
            border: none;
            font-size: 28px;
            cursor: pointer;
            color: #999;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.2s;
        }
        
        .close-modal-btn:hover {
            background: #f0f0f0;
            color: #333;
        }
        
        .markers-list-container {
            padding: 10px 20px 20px 20px;
            overflow-y: auto;
            flex: 1;
        }
        
        .marker-item {
            padding: 12px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
            border-radius: 8px;
        }
        
        .marker-item:hover {
            background: #f5f5f5;
        }
        
        .marker-info {
            flex: 1;
        }
        
        .marker-info b {
            font-size: 15px;
            color: #333;
        }
        
        .marker-info small {
            font-size: 11px;
            color: #999;
        }
        
        .delete-marker-btn {
            background: #ff4444;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.2s;
        }
        
        .delete-marker-btn:hover {
            background: #cc0000;
        }
        
        .empty-message {
            text-align: center;
            color: #999;
            padding: 40px 20px;
        }
        
        /* Адаптация для телефонов */
        @media (max-width: 768px) {
            .controls {
                width: 220px;
                top: 10px;
                right: 10px;
                padding: 10px;
            }
            
            .controls h4 {
                font-size: 13px;
            }
            
            .controls input, .controls button {
                font-size: 12px;
                padding: 6px;
            }
            
            .show-list-btn {
                bottom: 15px;
                left: 15px;
                padding: 10px 16px;
                font-size: 14px;
            }
            
            .music-control {
                bottom: 15px;
                right: 15px;
                padding: 8px 12px;
                font-size: 12px;
            }
            
            .markers-modal-content {
                width: 95%;
                max-height: 75vh;
            }
        }

        /* ========== ПРИВЕТСТВЕННОЕ ОКНО НА ВЕСЬ ЭКРАН ========== */
        .welcome-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('b1b2b90663f5d8b5f36c53166e61777d.png');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            z-index: 3000;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: opacity 0.5s ease;
        }
        
        /* Темный оверлей поверх фона для читаемости */
        .welcome-modal::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1;
        }
        
        .welcome-content {
            position: relative;
            z-index: 2;
            text-align: center;
            max-width: 700px;
            width: 90%;
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Аватар - БОЛЬШОЙ 250px */
        .avatar {
            width: 250px !important;
            height: 250px !important;
            margin: 0 auto 20px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 5px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            animation: avatarFloat 3s ease-in-out infinite;
        }
        
        @keyframes avatarFloat {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-10px);
            }
        }
        
        .avatar img {
            width: 100% !important;
            height: 100% !important;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid white;
        }
        
        /* Пустое фото (заглушка) */
        .empty-photo {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 90px;
            color: #999;
            border: 3px solid white;
        }
        
        /* Облачко диалога */
        .dialog-bubble {
            background: white;
            border-radius: 30px;
            padding: 20px 30px;
            margin: 20px auto;
            position: relative;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            max-width: 350px;
        }
        
        .dialog-bubble::before {
            content: '';
            position: absolute;
            top: -15px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 15px solid transparent;
            border-right: 15px solid transparent;
            border-bottom: 20px solid white;
        }
        
        .dialog-bubble p {
            font-size: 18px;
            color: #333;
            line-height: 1.5;
            margin: 0;
        }
        
        .dialog-bubble .small-text {
            font-size: 13px;
            color: #999;
            margin-top: 8px;
        }
        
        /* Кнопка закрытия */
        .close-welcome-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 35px;
            border: none;
            border-radius: 40px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        .close-welcome-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(102,126,234,0.4);
        }
        
        /* Адаптация для телефонов */
        @media (max-width: 768px) {
            .avatar {
                width: 200px !important;
                height: 200px !important;
            }
            
            .empty-photo {
                font-size: 70px;
            }
            
            .dialog-bubble {
                padding: 15px 25px;
                max-width: 280px;
            }
            
            .dialog-bubble p {
                font-size: 16px;
            }
            
            .close-welcome-btn {
                padding: 12px 30px;
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <div id="map"></div>

    <!-- Аудиоплеер для фоновой музыки -->
    <audio id="bgMusic" loop preload="auto">
        <source src="/music.mp3" type="audio/mpeg">
    </audio>

    <!-- ПРИВЕТСТВЕННОЕ ОКНО НА ВЕСЬ ЭКРАН -->
    <div id="welcomeModal" class="welcome-modal">
        <div class="welcome-content">
            <!-- Аватар с пустым фото -->
            <div class="avatar" id="avatarTest">
                <div class="empty-photo" id="avatarPlaceholder">
                    🧙‍♂️
                </div>
                <img id="avatarImg" style="display: none;" alt="Аватар">
            </div>
            
            <!-- Облачко диалога -->
            <div class="dialog-bubble">
                <p>🌟 Добро пожаловать в Карту Событий! 🌟</p>
                <div class="small-text">✨ Я ваш гид по этому приключению ✨</div>
            </div>
            
            <!-- Кнопка закрытия (теперь запускает музыку) -->
            <button class="close-welcome-btn" onclick="startJourney()">
                Начать путешествие →
            </button>
        </div>
    </div>

    <!-- Панель добавления меток (справа вверху) -->
    <div class="controls">
        <h4>➕ Добавить метку</h4>
        <input type="text" id="markerName" placeholder="Название метки">
        <button onclick="addMarkerByCoords()">Добавить по координатам</button>
        <small>Или кликните по карте</small>
    </div>

    <!-- Кнопка вызова списка меток -->
    <button class="show-list-btn" onclick="openMarkersList()">
        📋 Список меток (<span id="markersCount">0</span>)
    </button>

    <!-- Кнопка управления музыкой (появляется после старта) -->
    <button id="musicControlBtn" class="music-control" style="display: none;" onclick="toggleMusic()">
        🔇 Музыка выкл
    </button>

    <!-- Модальное окно со списком меток -->
    <div id="markersModal" class="markers-modal">
        <div class="markers-modal-content">
            <div class="markers-modal-header">
                <h3>📌 Мои метки</h3>
                <button class="close-modal-btn" onclick="closeMarkersList()">&times;</button>
            </div>
            <div class="markers-list-container">
                <div id="markersList"></div>
            </div>
        </div>
    </div>

    <script>
        // ОТЛАДКА: Проверка размера аватара
        window.addEventListener('load', function() {
            var avatar = document.getElementById('avatarTest');
            if (avatar) {
                var width = avatar.offsetWidth;
                console.log('Размер аватара: ' + width + 'px');
                if (width < 200) {
                    console.warn('Аватар слишком маленький! Должен быть 250px, а он ' + width + 'px');
                } else {
                    console.log('✅ Аватар увеличен до ' + width + 'px');
                }
            }
        });

        // Инициализация карты
        var map = L.map('map').setView([55.751244, 37.618423], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        var markers = {};
        var nextId = 0;
        
        // Музыкальные переменные
        var audio = document.getElementById('bgMusic');
        var musicControlBtn = document.getElementById('musicControlBtn');
        var isMusicPlaying = false;
        var musicStarted = false;

        // Функция запуска музыки (вызывается при старте путешествия)
        function startMusic() {
            if (!musicStarted) {
                audio.play().then(() => {
                    isMusicPlaying = true;
                    musicStarted = true;
                    musicControlBtn.style.display = 'flex';
                    musicControlBtn.innerHTML = '🎵 Музыка вкл';
                    musicControlBtn.style.background = 'rgba(76, 175, 80, 0.9)';
                }).catch(error => {
                    console.log('Автовоспроизведение заблокировано:', error);
                    musicControlBtn.style.display = 'flex';
                    musicControlBtn.innerHTML = '🔇 Нажмите для музыки';
                    musicControlBtn.style.background = 'rgba(0, 0, 0, 0.7)';
                });
            }
        }
        
        // Функция переключения музыки
        function toggleMusic() {
            if (isMusicPlaying) {
                audio.pause();
                isMusicPlaying = false;
                musicControlBtn.innerHTML = '🔇 Музыка выкл';
                musicControlBtn.style.background = 'rgba(0, 0, 0, 0.7)';
            } else {
                audio.play().then(() => {
                    isMusicPlaying = true;
                    musicControlBtn.innerHTML = '🎵 Музыка вкл';
                    musicControlBtn.style.background = 'rgba(76, 175, 80, 0.9)';
                }).catch(error => {
                    console.log('Не удалось запустить музыку:', error);
                });
            }
        }

        // Функция начала путешествия (закрывает окно и запускает музыку)
        function startJourney() {
            closeWelcomeModal();
            startMusic();
        }

        // Функция для загрузки аватара (если есть)
        function loadAvatar() {
            fetch('/avatar.jpg')
                .then(response => {
                    if (response.ok) {
                        return response.blob();
                    }
                    throw new Error('Нет фото');
                })
                .then(blob => {
                    const url = URL.createObjectURL(blob);
                    const img = document.getElementById('avatarImg');
                    const placeholder = document.getElementById('avatarPlaceholder');
                    img.src = url;
                    img.style.display = 'block';
                    placeholder.style.display = 'none';
                })
                .catch(() => {
                    console.log('Используется стандартный аватар');
                });
        }

        // Функции для модального окна со списком
        function openMarkersList() {
            const modal = document.getElementById('markersModal');
            modal.classList.add('active');
            updateMarkersCount();
        }
        
        function closeMarkersList() {
            const modal = document.getElementById('markersModal');
            modal.classList.remove('active');
        }
        
        // Обновление счетчика меток на кнопке
        function updateMarkersCount() {
            const count = Object.keys(markers).length;
            const countSpan = document.getElementById('markersCount');
            if (countSpan) countSpan.textContent = count;
        }

        // Функция закрытия приветственного окна
        function closeWelcomeModal() {
            const modal = document.getElementById('welcomeModal');
            modal.style.opacity = '0';
            setTimeout(() => {
                modal.style.display = 'none';
            }, 500);
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
                updateMarkersCount();
            } catch(e) { console.log(e); }
        }

        function addMarkerToMap(id, lat, lng, name) {
            var marker = L.marker([lat, lng]).addTo(map);
            marker.bindPopup("<b>" + name + "</b><br>" + lat.toFixed(5) + ", " + lng.toFixed(5));
            markers[id] = { marker: marker, lat: lat, lng: lng, name: name };
            updateList();
            updateMarkersCount();
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
                updateMarkersCount();
            }
        }

        function updateList() {
            var listDiv = document.getElementById('markersList');
            if (!listDiv) return;
            
            listDiv.innerHTML = '';
            
            const markersArray = Object.entries(markers);
            if (markersArray.length === 0) {
                listDiv.innerHTML = '<div class="empty-message">✨ Нет меток<br>Кликните по карте, чтобы добавить</div>';
                return;
            }
            
            for (let [id, m] of markersArray) {
                let div = document.createElement('div');
                div.className = 'marker-item';
                div.innerHTML = `
                    <div class="marker-info">
                        <b>${escapeHtml(m.name)}</b><br>
                        <small>${m.lat.toFixed(5)}, ${m.lng.toFixed(5)}</small>
                    </div>
                    <button class="delete-marker-btn" data-id="${id}">🗑️</button>
                `;
                
                div.onclick = (function(lat, lng) { 
                    return function(e) {
                        if (e.target.classList && e.target.classList.contains('delete-marker-btn')) return;
                        map.setView([lat, lng], 15);
                        closeMarkersList();
                    };
                })(m.lat, m.lng);
                
                const delBtn = div.querySelector('.delete-marker-btn');
                delBtn.onclick = (function(id) { return function(e) {
                    e.stopPropagation();
                    deleteMarker(id);
                }; })(id);
                
                listDiv.appendChild(div);
            }
        }
        
        // Простая защита от XSS
        function escapeHtml(str) {
            return str.replace(/[&<>]/g, function(m) {
                if (m === '&') return '&amp;';
                if (m === '<') return '&lt;';
                if (m === '>') return '&gt;';
                return m;
            });
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

        map.on('click', function(e) {
            let name = prompt("Название метки:", "Новое событие");
            if (name) addMarker(e.latlng.lat, e.latlng.lng, name);
        });

        // Закрытие модального окна по клику на фон
        document.getElementById('markersModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeMarkersList();
            }
        });
        
        // Загружаем аватар и метки
        loadAvatar();
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
        elif self.path == '/avatar.jpg':
            try:
                with open('avatar.jpg', 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/jpeg')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
        elif self.path == '/music.mp3':
            try:
                with open('music.mp3', 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'audio/mpeg')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
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
        print(f"🎵 Музыка запустится после нажатия 'Начать путешествие'")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()

