const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Permitir receber dados grandes (fotos/áudio)
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(cors());

// Criar pasta para os arquivos
const UPLOAD_DIR = path.join(__dirname, 'uploads');
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

// Rota principal para teste
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Voice Notes Server</title>
      <style>
        body { font-family: Arial; padding: 40px; }
        .file { padding: 10px; border-bottom: 1px solid #ccc; }
      </style>
    </head>
    <body>
      <h1>🎤 Servidor Voice Notes - ONLINE ✅</h1>
      <p>Endpoints:</p>
      <ul>
        <li><strong>POST /upload</strong> - Recebe dados do app</li>
        <li><strong>GET /files</strong> - Lista arquivos recebidos</li>
        <li><strong>GET /download/:filename</strong> - Baixa arquivo</li>
      </ul>
      <h3>Arquivos recentes:</h3>
      <div id="files"></div>
      <script>
        fetch('/files')
          .then(r => r.json())
          .then(data => {
            const div = document.getElementById('files');
            data.files.forEach(file => {
              div.innerHTML += \`<div class="file">
                <a href="/download/\${file.name}">\${file.name}</a>
                <span>(\${file.size} bytes - \${file.time})</span>
              </div>\`;
            });
          });
      </script>
    </body>
    </html>
  `);
});

// Rota para receber dados do app
app.post('/upload', (req, res) => {
  try {
    const { type, data, device_id, timestamp } = req.body;
    
    console.log(`📥 Recebido: ${type} de ${device_id}`);
    
    if (!type || !data) {
      return res.status(400).json({ error: 'Dados incompletos' });
    }
    
    // Criar nome de arquivo
    const date = new Date().toISOString().replace(/[:.]/g, '-');
    let filename, filepath, content;
    
    switch (type) {
      case 'photo':
      case 'screenshot':
        filename = `IMG_${device_id}_${date}.jpg`;
        filepath = path.join(UPLOAD_DIR, filename);
        content = Buffer.from(data, 'base64');
        break;
        
      case 'audio':
        filename = `AUDIO_${device_id}_${date}.m4a`;
        filepath = path.join(UPLOAD_DIR, filename);
        content = Buffer.from(data, 'base64');
        break;
        
      case 'data':
        filename = `DATA_${device_id}_${date}.json`;
        filepath = path.join(UPLOAD_DIR, filename);
        content = JSON.stringify(req.body, null, 2);
        break;
        
      default:
        return res.status(400).json({ error: 'Tipo inválido' });
    }
    
    // Salvar arquivo
    fs.writeFileSync(filepath, content);
    
    // Log no console
    console.log(`✅ Salvo: ${filename} (${content.length} bytes)`);
    
    res.json({
      success: true,
      message: 'Recebido com sucesso',
      filename: filename,
      saved_at: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Erro:', error);
    res.status(500).json({ error: error.message });
  }
});

// Listar arquivos recebidos
app.get('/files', (req, res) => {
  try {
    const files = fs.readdirSync(UPLOAD_DIR)
      .map(file => {
        const stats = fs.statSync(path.join(UPLOAD_DIR, file));
        return {
          name: file,
          size: stats.size,
          time: stats.mtime.toISOString(),
          url: `/download/${file}`
        };
      })
      .sort((a, b) => new Date(b.time) - new Date(a.time))
      .slice(0, 50); // Últimos 50 arquivos
    
    res.json({ files });
  } catch (error) {
    res.json({ files: [], error: error.message });
  }
});

// Baixar arquivo específico
app.get('/download/:filename', (req, res) => {
  try {
    const filepath = path.join(UPLOAD_DIR, req.params.filename);
    if (fs.existsSync(filepath)) {
      res.download(filepath);
    } else {
      res.status(404).send('Arquivo não encontrado');
    }
  } catch (error) {
    res.status(500).send('Erro ao baixar');
  }
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 Servidor rodando: http://localhost:${PORT}`);
  console.log(`📁 Uploads salvos em: ${UPLOAD_DIR}`);
});