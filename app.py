from flask import Flask, request, jsonify
from flask_cors import CORS
from db.BD import get_connection, get_cursor
import hashlib
from controlador.c_usuario import UsuarioController
from controlador.eval_c import EvaluacionController
from datetime import date, timedelta
import os

app = Flask(__name__)
CORS(app)

# =========================================
# RUTAS DE USUARIO
# =========================================

@app.route('/login', methods=['POST'])
def login():
    return UsuarioController.login()

@app.route('/register', methods=['POST'])
def register():
    return UsuarioController.register()

# =========================================
# RUTAS DE PREGUNTAS
# =========================================

@app.route('/preguntas/hads', methods=['GET'])
def obtener_preguntas_hads():
    return EvaluacionController.obtener_preguntas_hads()

@app.route('/preguntas/ders', methods=['GET'])
def obtener_preguntas_ders():
    return EvaluacionController.obtener_preguntas_ders()

# =========================================
# RUTAS DE VERIFICACIÓN
# =========================================

@app.route('/verificar/hads', methods=['POST'])
def verificar_hads():
    return EvaluacionController.verificar_hads()

@app.route('/verificar/ders', methods=['POST'])
def verificar_ders():
    return EvaluacionController.verificar_ders()

# =========================================
# RUTAS DE EVALUACIONES
# =========================================

@app.route('/evaluacion/nueva', methods=['POST'])
def evaluacion_nueva():
    return EvaluacionController.crear_evaluacion()

@app.route('/evaluacion/ders/nueva', methods=['POST'])
def evaluacion_ders_nueva():
    return EvaluacionController.crear_evaluacion()

@app.route('/evaluacion/guardar', methods=['POST'])
def guardar_respuestas():
    return EvaluacionController.guardar_respuestas()

@app.route('/evaluacion/hads/guardar', methods=['POST'])
def guardar_respuestas_hads():
    return EvaluacionController.guardar_respuestas()

@app.route('/evaluacion/ders/guardar', methods=['POST'])
def guardar_respuestas_ders():
    return EvaluacionController.guardar_respuestas()

# =========================================
# RESULTADOS
# =========================================

@app.route('/evaluaciones/usuario/<int:id_usuario>', methods=['GET'])
def obtener_evaluaciones_usuario(id_usuario):
    return EvaluacionController.obtener_evaluaciones_usuario(id_usuario)

# Ruta para detalle de evaluación HADS
@app.route('/evaluacion/hads/<int:id_evaluacion>', methods=['GET'])
def obtener_detalle_hads(id_evaluacion):
    return EvaluacionController.obtener_detalle_hads(id_evaluacion)

# Ruta para detalle de evaluación DERS
@app.route('/evaluacion/ders/<int:id_evaluacion>', methods=['GET'])
def obtener_detalle_ders(id_evaluacion):
    return EvaluacionController.obtener_detalle_ders(id_evaluacion)

# Ruta genérica para detalle (mantener compatibilidad)
@app.route('/evaluacion/<int:id_evaluacion>/<string:tipo>', methods=['GET'])
def obtener_detalle_evaluacion(id_evaluacion, tipo):
    if tipo.upper() == 'HADS':
        return EvaluacionController.obtener_detalle_hads(id_evaluacion)
    else:
        return EvaluacionController.obtener_detalle_ders(id_evaluacion)

# =========================================
# EMOCIONES
# =========================================

@app.route('/emociones/obtener', methods=['GET'])
def obtener_emociones():
    return EvaluacionController.obtener_emociones()

@app.route('/emociones/registrar', methods=['POST'])
def registrar_emocion():
    return EvaluacionController.registrar_emocion()

@app.route('/emociones/test/<int:id_usuario>', methods=['GET'])
def test_emociones(id_usuario):
    """Ruta de prueba para emociones"""
    print(f"🧪 Ruta test_emociones llamada con usuario: {id_usuario}")
    return jsonify({
        "success": True,
        "message": f"Ruta funcionando para usuario {id_usuario}",
        "data": [
            {"emocionGeneral": "Alegría", "emocionEspecifica": "Éxtasis", "tipo": "predominante"},
            {"emocionGeneral": "Confianza", "emocionEspecifica": "Admiración", "tipo": "predominante"}
        ]
    })

@app.route('/emociones/registros/<int:id_usuario>', methods=['GET'])
def obtener_registros_emociones_directo(id_usuario):
    """Ruta directa para obtener registros de emociones"""
    try:
        dias = request.args.get('dias', 30, type=int)
        print(f"📥 Ruta directa - Usuario: {id_usuario}, Días: {dias}")
        
        fecha_limite = date.today() - timedelta(days=dias)
        
        conn = get_connection()
        cursor = get_cursor(conn) 
        
        cursor.execute("""
            SELECT 
                re.id_registro as id,
                re.tipo_registro as tipo,
                re.momento,
                re.fecha,
                re.comentario,
                ec.emocion as emocionGeneral,
                ee.emocion as emocionEspecifica
            FROM registro_emociones_usuario re
            LEFT JOIN emocionescat ec ON re.id_emocion_general = ec.id_emocion
            LEFT JOIN emocion_espe ee ON re.id_emocion_especifica = ee.id_espe
            WHERE re.id_usuario = %s AND re.fecha >= %s
            ORDER BY re.fecha DESC
        """, (id_usuario, fecha_limite))
        
        registros = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convertir fechas a string
        for registro in registros:
            if registro.get('fecha'):
                registro['fecha'] = str(registro['fecha'])
        
        print(f"✅ Encontrados {len(registros)} registros")
        
        return jsonify({
            "success": True,
            "registros": registros
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

# =========================================
# BIOMARCADORES
# =========================================

@app.route('/guardar_biomarcadores', methods=['POST'])
def guardar_biomarcadores():
    """
    Guarda los biomarcadores diarios del usuario
    Espera JSON: {
        "id_usuario": int,
        "fecha": "YYYY-MM-DD",
        "pasos": int,
        "ritmo_cardiaco": int (opcional),
        "sueno_minutos": int,
        "hrv_ms": float
    }
    """
    try:
        data = request.get_json()
        print(f"📊 Recibiendo biomarcadores: {data}")
        
        id_usuario = data.get('id_usuario')
        fecha = data.get('fecha')
        pasos = data.get('pasos', 0)
        ritmo_cardiaco = data.get('ritmo_cardiaco')
        sueno_minutos = data.get('sueno_minutos', 0)
        hrv_ms = data.get('hrv_ms', 0.0)
        
        # Validar datos requeridos
        if not id_usuario:
            return jsonify({'error': 'id_usuario es requerido'}), 400
        if not fecha:
            return jsonify({'error': 'fecha es requerida'}), 400
        
        # Validar que el usuario existe
        conn = get_connection()
        cursor = get_cursor(conn)  # ✅ CORREGIDO
        
        cursor.execute("SELECT id_usuario FROM usuario WHERE id_usuario = %s", (id_usuario,))
        usuario = cursor.fetchone()
        
        if not usuario:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Verificar si ya existe un registro para esta fecha
        cursor.execute("""
            SELECT id FROM biomarcadores_diarios 
            WHERE id_usuario = %s AND fecha = %s
        """, (id_usuario, fecha))
        
        existe = cursor.fetchone()
        
        if existe:
            # Actualizar registro existente
            cursor.execute("""
                UPDATE biomarcadores_diarios 
                SET pasos = %s,
                    ritmo_cardiaco = %s,
                    sueno_minutos = %s,
                    hrv_ms = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_usuario = %s AND fecha = %s
            """, (pasos, ritmo_cardiaco, sueno_minutos, hrv_ms, id_usuario, fecha))
            mensaje = "Biomarcadores actualizados correctamente"
        else:
            # Insertar nuevo registro
            cursor.execute("""
                INSERT INTO biomarcadores_diarios 
                (id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms))
            mensaje = "Biomarcadores guardados correctamente"
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'mensaje': mensaje,
            'success': True
        }), 200
        
    except Exception as e:
        print(f"❌ Error al guardar biomarcadores: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/obtener_biomarcadores/<int:id_usuario>', methods=['GET'])
def obtener_biomarcadores(id_usuario):
    """
    Obtiene los biomarcadores de un usuario
    Parámetros opcionales: ?fecha=YYYY-MM-DD o ?dias=30
    """
    try:
        fecha = request.args.get('fecha')
        dias = request.args.get('dias', 30, type=int)
        
        conn = get_connection()
        cursor = get_cursor(conn)  # ✅ CORREGIDO
        
        if fecha:
            # Obtener biomarcadores de una fecha específica
            cursor.execute("""
                SELECT id, id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms, created_at
                FROM biomarcadores_diarios 
                WHERE id_usuario = %s AND fecha = %s
                ORDER BY fecha DESC
            """, (id_usuario, fecha))
        else:
            # Obtener biomarcadores de los últimos N días
            cursor.execute("""
                SELECT id, id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms, created_at
                FROM biomarcadores_diarios 
                WHERE id_usuario = %s 
                ORDER BY fecha DESC
                LIMIT %s
            """, (id_usuario, dias))
        
        registros = cursor.fetchall()
        
        # Convertir fechas a string
        for registro in registros:
            if registro.get('fecha'):
                registro['fecha'] = str(registro['fecha'])
            if registro.get('created_at'):
                registro['created_at'] = str(registro['created_at'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'biomarcadores': registros,
            'total': len(registros)
        }), 200
        
    except Exception as e:
        print(f"❌ Error al obtener biomarcadores: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/biomarcador_ultimo/<int:id_usuario>', methods=['GET'])
def obtener_ultimo_biomarcador(id_usuario):
    """Obtiene el último biomarcador registrado del usuario"""
    try:
        conn = get_connection()
        cursor = get_cursor(conn)  # ✅ CORREGIDO
        
        cursor.execute("""
            SELECT id, id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms, created_at
            FROM biomarcadores_diarios 
            WHERE id_usuario = %s 
            ORDER BY fecha DESC
            LIMIT 1
        """, (id_usuario,))
        
        registro = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if registro:
            if registro.get('fecha'):
                registro['fecha'] = str(registro['fecha'])
            if registro.get('created_at'):
                registro['created_at'] = str(registro['created_at'])
            return jsonify({'success': True, 'biomarcador': registro}), 200
        else:
            return jsonify({'success': True, 'biomarcador': None, 'message': 'No hay registros'}), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =========================================
# RUTA DE PRUEBA
# =========================================

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "Servidor funcionando"}), 200

# =========================================
# MANEJO DE ERRORES
# =========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Ruta no encontrada"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "Error interno del servidor"}), 500


if __name__ == '__main__':
    # Detectar si está en Render (producción) o local
    is_production = os.getenv('RENDER', False)
    
    if is_production:
        # En producción, usar el puerto que asigna Render
        port = int(os.getenv('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        # En desarrollo local
        print("\n" + "="*50)
        print("🚀 SERVIDOR MVC INICIADO")
        print("="*50)
        print("📡 Escuchando en: http://0.0.0.0:5000")
        print("🔧 Modo: Debug")
        print("\n📋 ENDPOINTS DISPONIBLES:")
        print("   POST /login")
        print("   POST /register")
        print("   GET  /preguntas/hads")
        print("   GET  /preguntas/ders")
        print("   POST /verificar/hads")
        print("   POST /verificar/ders")
        print("   POST /evaluacion/nueva")
        print("   POST /evaluacion/ders/nueva")
        print("   POST /evaluacion/guardar")
        print("   GET  /evaluaciones/usuario/<id>")
        print("   GET  /evaluacion/hads/<id>")
        print("   GET  /evaluacion/ders/<id>")
        print("   GET  /evaluacion/<id>/<tipo>")
        print("   GET  /emociones/obtener")
        print("   POST /emociones/registrar")
        print("   GET  /emociones/registros/<id>")
        print("   POST /guardar_biomarcadores")
        print("   GET  /obtener_biomarcadores/<id>")
        print("   GET  /biomarcador_ultimo/<id>")
        print("="*50 + "\n")
        
        app.run(host='0.0.0.0', port=5000, debug=True)

