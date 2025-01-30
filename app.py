import os
import mysql.connector
import re
from flask import Flask, jsonify, request
from datetime import datetime
from flask_cors import CORS  # Importar CORS

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

# Configuración mejorada de la base de datos
DB_CONFIG = {
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'host': os.environ.get('MYSQL_HOST'),
    'database': os.environ.get('MYSQL_DATABASE'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'ssl_ca': os.environ.get('MYSQL_SSL_CA') or None  # SSL opcional
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        raise RuntimeError(f"Error connecting to MySQL: {err}")

# Validaciones comunes
def validar_ruc(ruc):
    if len(ruc) != 11 or not ruc.isdigit():
        raise ValueError("RUC debe tener 11 dígitos numéricos")

def procesar_datos(data):
    return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}

# Endpoint para crear registros
@app.route('/crear', methods=['POST'])
def crear_registro():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos JSON requeridos'}), 400
        
        # Validar campos obligatorios
        campos_requeridos = ['ruc', 'nom_emp', 'fecha_doc', 'boleta_factura']
        for campo in campos_requeridos:
            if campo not in data or not str(data[campo]).strip():
                return jsonify({'success': False, 'error': f'Campo requerido: {campo}'}), 400
        
        validar_ruc(data['ruc'])
        data = procesar_datos(data)

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
            data.get('tipo_comprobante', ''),
            data.get('descripcion', ''),
            data.get('metodo_pago', ''),
            data.get('monto_total', 0),
            data.get('monto_pagado', 0),
            data.get('monto_pendiente', 0),
            data.get('estado', 'Pendiente'),
            data.get('datos_extras', None)
        )
        
        cursor.execute(query, values)
        connection.commit()
        nuevo_id = cursor.lastrowid
        
        # Obtener registro creado
        cursor.execute("SELECT * FROM comp_general WHERE id = %s", (nuevo_id,))
        nuevo_registro = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Registro creado exitosamente',
            'data': nuevo_registro
        }), 201
        
    except mysql.connector.IntegrityError as e:
        return jsonify({'success': False, 'error': 'Error de integridad: Posible duplicado de RUC'}), 409
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Endpoint para modificar registros
@app.route('/modificar/<int:id>', methods=['PUT'])
def modificar_registro(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos JSON requeridos'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Verificar existencia del registro
        cursor.execute("SELECT id FROM comp_general WHERE id = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Registro no encontrado'}), 404

        # Validar y procesar datos
        if 'ruc' in data:
            validar_ruc(data['ruc'])
        data = procesar_datos(data)
        
        # Construir actualización
        campos_permitidos = [
            'ruc', 'nom_emp', 'fecha_doc', 'boleta_factura',
            'tipo_comprobante', 'descripcion', 'metodo_pago',
            'monto_total', 'monto_pagado', 'monto_pendiente',
            'estado', 'datos_extras'
        ]
        
        updates = []
        values = []
        for campo in campos_permitidos:
            if campo in data:
                updates.append(f"{campo} = %s")
                values.append(data[campo])
        
        if not updates:
            return jsonify({'success': False, 'error': 'No hay campos válidos para actualizar'}), 400
        
        query = f"UPDATE comp_general SET {', '.join(updates)} WHERE id = %s"
        values.append(id)
        
        cursor.execute(query, values)
        connection.commit()
        
        # Obtener registro actualizado
        cursor.execute("SELECT * FROM comp_general WHERE id = %s", (id,))
        registro_actualizado = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Registro actualizado exitosamente',
            'data': registro_actualizado
        }), 200
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'error': f'Error MySQL: {e}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
            'data': registros,
            'total': len(registros)
        }), 200
        
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'error': f'Error MySQL: {e}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', 
            port=os.environ.get('PORT', 5000),
            debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')
