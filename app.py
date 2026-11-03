from flask import Flask, render_template_string, request
import socket
import re

app = Flask(__name__)

# Lista para almacenar los dispositivos conectados
dispositivos_conectados = []

# Función auxiliar para interpretar el User-Agent y mostrar un nombre de dispositivo amigable
def parsear_user_agent(ua_string):
    if not ua_string:
        return "Dispositivo Desconocido"
    
    # Detección básica de sistemas operativos comunes
    if "iPhone" in ua_string or "iPad" in ua_string:
        so = "iOS (Apple)"
    elif "Android" in ua_string:
        so = "Android"
    elif "Windows" in ua_string:
        so = "Windows PC"
    elif "Macintosh" in ua_string or "Mac OS X" in ua_string:
        so = "Mac / macOS"
    elif "Linux" in ua_string:
        so = "Linux"
    else:
        so = "Otro Sistema"
        
    return so

# Plantilla HTML del Portal (Pantalla de bienvenida simple)
html_portal = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Wi-Fi Gratuito - Demostración Ética</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: white; text-align: center; padding-top: 50px; }
        .box { background: #1e293b; max-width: 400px; margin: auto; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        .btn { display: inline-block; background: #38bdf8; color: #0f172a; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 5px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Red de Prueba Activa</h2>
        <p>Has accedido exitosamente al servidor de demostración de la clase de ética.</p>
        <a href="/conectado" class="btn">Continuar Navegación</a>
    </div>
</body>
</html>
"""

# Plantilla HTML del Panel de Control en Vivo
html_admin = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3"> <!-- Se actualiza automáticamente cada 3 segundos -->
    <title>Panel de Monitoreo en Vivo</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: white; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #1e293b; }
        th, td { padding: 12px; border: 1px solid #334155; text-align: left; }
        th { background: #38bdf8; color: #0f172a; }
        .code { font-family: monospace; color: #38bdf8; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>Panel de Control - Dispositivos Detectados</h1>
    <p>Captura automática basada en solicitudes HTTP a la IP del servidor:</p>
    <table>
        <tr>
            <th>Dirección IP</th>
            <th>Tipo de Dispositivo (Detectado)</th>
            <th>Hostname de Red</th>
            <th>User-Agent Completo</th>
        </tr>
        {% for d in dispositivos %}
        <tr>
            <td><strong>{{ d.ip }}</strong></td>
            <td>{{ d.tipo_dispositivo }}</td>
            <td class="code">{{ d.hostname }}</td>
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
    
    # Interpretar el dispositivo mediante el User-Agent
    tipo_dispositivo = parsear_user_agent(user_agent)
    
    # Intentar obtener el hostname por DNS inverso en la red local
    try:
        hostname_red = socket.gethostbyaddr(ip_cliente)[0]
    except (socket.herror, socket.gaierror, Exception):
        hostname_red = "No disponible / Bloqueado"
        
    info_dispositivo = {
        'ip': ip_cliente,
        'tipo_dispositivo': tipo_dispositivo,
        'hostname': hostname_red,
        'user_agent': user_agent
    }
    
    # Evitar duplicados saturando la tabla si recargan la página varias veces
    # Si la IP ya existe, actualizamos su última visita por si cambió de navegador o datos
    existente = next((d for d in dispositivos_conectados if d['ip'] == ip_cliente), None)
    if not existente:
        dispositivos_conectados.append(info_dispositivo)
        
    return render_template_string(html_portal)

@app.route('/conectado')
def conectado():
    return "<h2 style='color:#4ade80; text-align:center; margin-top:50px;'>¡Conexión registrada en el panel del expositor!</h2>"

@app.route('/admin')
def admin():
    return render_template_string(html_admin, dispositivos=dispositivos_conectados)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
