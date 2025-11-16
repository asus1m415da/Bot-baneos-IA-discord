from flask import Flask, render_template, request, jsonify
import threading
import os
import json

app = Flask(__name__)

# Almacena claves generadas
keys = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/banear', methods=['POST'])
def banear():
    data = request.json
    key = data.get('key')
    server = data.get('server')
    users = data.get('users')
    if key not in keys:
        return jsonify({'error': 'Clave inválida'}), 400
    # Aquí iría la lógica para banear usuarios
    return jsonify({'message': 'Usuarios baneados'})

@app.route('/banear_manual', methods=['POST'])
def banear_manual():
    data = request.json
    key = data.get('key')
    server = data.get('server')
    user = data.get('user')
    if key not in keys:
        return jsonify({'error': 'Clave inválida'}), 400
    # Aquí iría la lógica para banear manualmente
    return jsonify({'message': 'Usuario baneado'})

if __name__ == '__main__':
    # Inicia el bot en un hilo separado
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    # Inicia la aplicación Flask
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
