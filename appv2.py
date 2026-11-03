from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Almacén de dispositivos conectados y comandos activos
dispositivos_conectados = []
comandos_por_ip = {}  # Diccionario para guardar qué imagen se le mandó a cada IP: { "192.168.1.X": "url_imagen" }

def parsear_user_agent(ua_string):
    if not ua_string:
        return "Dispositivo Desconocido"
    if "iPhone" in ua_string or "iPad" in ua_string:
        return "iOS (Apple)"
    elif "Android" in ua_string:
        return "Android"
    elif "Windows" in ua_string:
        return "Windows PC"
    elif "Macintosh" in ua_string or "Mac OS X" in ua_string:
        return "Mac / macOS"
    elif "Linux" in ua_string:
        return "Linux"
    return "Otro Sistema"

# Plantilla HTML del Portal (Con sistema de escucha en tiempo real para la imagen)
html_portal = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Wi-Fi Gratuito - Demostración Ética</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: white; text-align: center; padding-top: 40px; margin: 0; }
        .box { background: #1e293b; max-width: 400px; margin: auto; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        .btn { display: inline-block; background: #38bdf8; color: #0f172a; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 5px; margin-top: 20px; }
        #contenedor-imagen { margin-top: 20px; display: none; }
        #contenedor-imagen img { max-width: 100%; border-radius: 8px; border: 2px solid #38bdf8; }
        .alerta { color: #38bdf8; font-size: 0.9em; margin-top: 15px; }
    </style>
    <script>
        // Función que revisa cada 2 segundos si el servidor le envió una imagen a esta IP
        setInterval(function() {
            fetch('/verificar-estado')
                .then(response => response.json())
                .then(data => {
                    if (data.imagen) {
                        document.getElementById('img-recibida').src = data.imagen;
                        document.getElementById('contenedor-imagen').style.display = 'block';
                        document.getElementById('texto-espera').innerText = "¡Imagen recibida desde el panel de control!";
                    }
                })
                .catch(error => console.log('Error al verificar estado:', error));
        }, 2000);
    </script>
</head>
<body>
    <div class="box">
        <h2>Red de Prueba Activa</h2>
        <p id="texto-espera">Conectado al servidor de demostración. Esperando instrucciones del expositor...</p>
        
        <div id="contenedor-imagen">
            <p class="alerta"><strong>Mensaje Visual del Expositor:</strong></p>
            <img id="img-recibida" src="" alt="Imagen enviada">
        </div>
        
        <a href="/conectado" class="btn">Finalizar / Navegar</a>
    </div>
</body>
</html>
"""

# Plantilla HTML del Panel de Control (Incluye la sección para enviar imágenes por IP)
html_admin = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3">
    <title>Panel de Monitoreo en Vivo</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: white; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #1e293b; }
        th, td { padding: 12px; border: 1px solid #334155; text-align: left; }
        th { background: #38bdf8; color: #0f172a; }
        .code { font-family: monospace; color: #38bdf8; font-size: 0.9em; }
        .form-envio { background: #1e293b; padding: 15px; border-radius: 8px; margin-top: 20px; border: 1px solid #334155; }
        input, select { padding: 8px; margin: 5px; background: #0f172a; color: white; border: 1px solid #334155; border-radius: 4px; }
        button { background: #38bdf8; color: #0f172a; border: none; padding: 9px 15px; font-weight: bold; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Panel de Control - Dispositivos Detectados</h1>
    
    <!-- Formulario para enviar imagen a una IP específica -->
    <div class="form-envio">
        <h3>Enviar Imagen a Dispositivo</h3>
        <form action="/enviar-imagen" method="POST">
            <label>IP del Destino:</label>
            <input type="text" name="ip_destino" placeholder="Ej. 192.168.1.15" required>
            
            <label>URL de la Imagen:</label>
            <input type="url" name="url_imagen" placeholder="https://ejemplo.com/imagen.jpg" style="width: 300px;" required>
            
            <button type="submit">Enviar Imagen</button>
        </form>
    </div>

    <table>
        <tr>
            <th>Dirección IP</th>
            <th>Tipo de Dispositivo</th>
            <th>Última Imagen Enviada</th>
            <th>User-Agent Completo</th>
        </tr>
        {% for d in dispositivos %}
        <tr>
            <td><strong>{{ d.ip }}</strong></td>
            <td>{{ d.tipo_dispositivo }}</td>
            <td class="code">{{ d.imagen_actual or "Ninguna" }}</td>
            <td class="code">{{ d.user_agent }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/')
def index():
    ip_cliente = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    tipo_dispositivo = parsear_user_agent(user_agent)
    
    # Registrar el dispositivo si es nuevo
    existente = next((d for d in dispositivos_conectados if d['ip'] == ip_cliente), None)
    if not existente:
        dispositivos_conectados.append({
            'ip': ip_cliente,
            'tipo_dispositivo': tipo_dispositivo,
            'user_agent': user_agent,
            'imagen_actual': None
        })
        
    return render_template_string(html_portal)

@app.route('/verificar-estado')
def verificar_estado():
    ip_cliente = request.remote_addr
    # Revisa si hay una imagen asignada a esta IP específica
    imagen = comandos_por_ip.get(ip_cliente, None)
    return jsonify({'imagen': imagen})

@app.route('/enviar-imagen', methods=['POST'])
def enviar_imagen():
    ip_destino = request.form.get('ip_destino')
    url_imagen = request.form.get('url_imagen')
    
    # Asignar la imagen a la IP en el diccionario de comandos
    if ip_destino:
        comandos_por_ip[ip_destino] = url_imagen
        
        # Actualizar el registro visual en la lista de dispositivos
        for d in dispositivos_conectados:
            if d['ip'] == ip_destino:
                d['imagen_actual'] = url_imagen
                
    return '<script>window.location.href="/admin";</script>'

@app.route('/conectado')
def conectado():
    return "<h2 style='color:#4ade80; text-align:center; margin-top:50px;'>¡Demostración finalizada con éxito!</h2>"

@app.route('/admin')
def admin():
    return render_template_string(html_admin, dispositivos=dispositivos_conectados)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
