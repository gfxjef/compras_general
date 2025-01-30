import os
import mysql.connector
from flask import Flask, jsonify, request
from datetime import datetime
from flask_cors import CORS  # Opcional para CORS

app = Flask(__name__)
CORS(app)  # Opcional: Habilitar CORS para desarrollo

# Configuración de la base de datos
DB_CONFIG = {
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'host': os.environ.get('MYSQL_HOST'),
    'database': os.environ.get('MYSQL_DATABASE'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        raise RuntimeError(f"Error connecting to MySQL: {err}")

# Endpoint para crear registros
@app.route('/crear', methods=['POST'])
def crear_registro():
    try:
        data = request.json
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            INSERT INTO comp_general (
                timestamp, ruc, nom_emp, fecha_doc, boleta_factura,
                tipo_comprobante, descripcion, metodo_pago, monto_total,
                monto_pagado, monto_pendiente, estado, datos_extras
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            datetime.now(),
            data['ruc'],
            data['nom_emp'],
            data['fecha_doc'],
            data['boleta_factura'],
            data['tipo_comprobante'],
            data['descripcion'],
            data['metodo_pago'],
            data['monto_total'],
            data['monto_pagado'],
            data['monto_pendiente'],
            data['estado'],
            data.get('datos_extras', None)
        )
        
        cursor.execute(query, values)
        connection.commit()
        nuevo_id = cursor.lastrowid
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Registro creado exitosamente',
            'id': nuevo_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Endpoint para modificar registros
@app.route('/modificar/<int:id>', methods=['PUT'])
def modificar_registro(id):
    try:
        data = request.json
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Construir la consulta dinámicamente
        updates = []
        values = []
        
        campos_permitidos = [
            'ruc', 'nom_emp', 'fecha_doc', 'boleta_factura',
            'tipo_comprobante', 'descripcion', 'metodo_pago',
            'monto_total', 'monto_pagado', 'monto_pendiente',
            'estado', 'datos_extras'
        ]
        
        for campo in campos_permitidos:
            if campo in data:
                updates.append(f"{campo} = %s")
                values.append(data[campo])
        
        if not updates:
            return jsonify({'success': False, 'error': 'No se proporcionaron campos para actualizar'}), 400
        
        query = f"UPDATE comp_general SET {', '.join(updates)} WHERE id = %s"
        values.append(id)
        
        cursor.execute(query, values)
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Registro no encontrado'}), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Registro actualizado exitosamente'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/registros', methods=['GET'])
def obtener_registros():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM comp_general")
        registros = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'registros': registros,
            'total': len(registros)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')
