from flask import Flask, request, jsonify
from flask_cors import CORS
from db.BD import get_connection, get_cursor
import hashlib
from controlador.c_usuario import UsuarioController
from controlador.eval_c import EvaluacionController
from sklearn.preprocessing import LabelEncoder
from datetime import date, timedelta
import pandas as pd
from xgboost import XGBClassifier
import os
import sys

app = Flask(__name__)
CORS(app)
# Configuración para Render
port = int(os.environ.get('PORT', 5000))
print(f"🚀 Iniciando servidor en puerto: {port}")

# Intentar cargar modelo XGBoost
try:
    from xgboost import XGBClassifier
    modelo_path = "modelo_xgboost.json"
    
    if os.path.exists(modelo_path):
        modelo = XGBClassifier()
        modelo.load_model(modelo_path)
        print("✅ Modelo XGBoost cargado correctamente")
    else:
        print(f"⚠️ No se encuentra el modelo en {modelo_path}")
        print(f"📁 Archivos disponibles: {os.listdir('.')}")
        modelo = None
except Exception as e:
    print(f"❌ Error cargando XGBoost: {str(e)}")
    modelo = None

# Definiciones
PREGUNTAS_ANSIEDAD = [1,3,5,7,9,11,13]
PREGUNTAS_DEPRESION = [2,4,6,8,10,12,14]
EMOCIONES_POSITIVAS = [1,2,8]
EMOCIONES_NEGATIVAS = [3,5,6,7]

# COLUMNAS DEL MODELO - Debe coincidir exactamente con lo que espera el modelo
COLUMNAS_MODELO = [
    "steps_mean", "steps_std", "steps_max", "steps_sum",
    "rr_mean", "rr_std", "rr_min", "rr_max",
    "heartrate_mean", "heartrate_std", "heartrate_min", "heartrate_max",
    "vfc_mean", "vfc_std", "vfc_min", "vfc_max",
    "deepsleeptime_max", "shallowsleeptime_max", "waketime_max", "remtime_max",
    "Ansiedad", "Depresion",
    "Emocion Normal predominante",
    "Emocion específica predominante",
    "Emocion extraordinaria general",
    "Emocion extraordinaria específica"
]
######## RUTAS DE USUARIO ##########


@app.route('/login', methods=['POST'])
def login():
    return UsuarioController.login()

@app.route('/register', methods=['POST'])
def register():
    return UsuarioController.register()

######### RUTAS DE PREGUNTAS ########

@app.route('/preguntas/hads', methods=['GET'])
def obtener_preguntas_hads():
    return EvaluacionController.obtener_preguntas_hads()

@app.route('/preguntas/ders', methods=['GET'])
def obtener_preguntas_ders():
    return EvaluacionController.obtener_preguntas_ders()

######### RUTAS DE VERIFICACIÓN ########

@app.route('/verificar/hads', methods=['POST'])
def verificar_hads():
    return EvaluacionController.verificar_hads()

@app.route('/verificar/ders', methods=['POST'])
def verificar_ders():
    return EvaluacionController.verificar_ders()

############ RUTAS DE EVALUACIONES ##########
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

############## RESULTADOS ##############

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

########### EMOCIONES ############

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
        
        print(f" Encontrados {len(registros)} registros")
        
        return jsonify({
            "success": True,
            "registros": registros
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

##### BIOMARCADORES ############
@app.route('/guardar_biomarcadores_estadisticas', methods=['POST'])
def guardar_biomarcadores_estadisticas():
    """
    Guarda las estadísticas de biomarcadores en la tabla registrobiomark
    Espera JSON con todos los campos de la tabla
    """
    try:
        data = request.get_json()
        print(f"Recibiendo biomarcadores: {data}")
        
        # Obtener datos del request
        id_usuario = data.get('id_usuario')
        fecha = data.get('fecha')
        
        # Validar datos requeridos
        if not id_usuario:
            return jsonify({'error': 'id_usuario es requerido'}), 400
        if not fecha:
            return jsonify({'error': 'fecha es requerida'}), 400
        
        # Validar que el usuario existe
        conn = get_connection()
        cursor = get_cursor(conn)
        
        cursor.execute("SELECT id_usuario FROM usuario WHERE id_usuario = %s", (id_usuario,))
        usuario = cursor.fetchone()
        
        if not usuario:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener todos los campos con valores por defecto
        steps_mean = data.get('steps_mean', 0.0)
        steps_std = data.get('steps_std', 0.0)
        steps_max = data.get('steps_max', 0)
        steps_sum = data.get('steps_sum', 0)
        
        rr_mean = data.get('rr_mean', 0.0)
        rr_std = data.get('rr_std', 0.0)
        rr_min = data.get('rr_min', 0)
        rr_max = data.get('rr_max', 0)
        
        heartrate_mean = data.get('heartrate_mean', 0.0)
        heartrate_std = data.get('heartrate_std', 0.0)
        heartrate_min = data.get('heartrate_min', 0)
        heartrate_max = data.get('heartrate_max', 0)
        
        vfc_mean = data.get('vfc_mean', 0.0)
        vfc_std = data.get('vfc_std', 0.0)
        vfc_min = data.get('vfc_min', 0)
        vfc_max = data.get('vfc_max', 0)
        
        deepsleeptime_max = data.get('deepsleeptime_max', 0.0)
        shallowsleeptime_max = data.get('shallowsleeptime_max', 0.0)
        waketime_max = data.get('waketime_max', 0.0)
        remtime_max = data.get('remtime_max', 0.0)
        
        # Verificar si ya existe un registro para esta fecha
        cursor.execute("""
            SELECT id FROM registrobiomark 
            WHERE id_usuario = %s AND fecha = %s
        """, (id_usuario, fecha))
        
        existe = cursor.fetchone()
        
        if existe:
            # Actualizar registro existente
            cursor.execute("""
                UPDATE registrobiomark 
                SET steps_mean = %s,
                    steps_std = %s,
                    steps_max = %s,
                    steps_sum = %s,
                    rr_mean = %s,
                    rr_std = %s,
                    rr_min = %s,
                    rr_max = %s,
                    heartrate_mean = %s,
                    heartrate_std = %s,
                    heartrate_min = %s,
                    heartrate_max = %s,
                    vfc_mean = %s,
                    vfc_std = %s,
                    vfc_min = %s,
                    vfc_max = %s,
                    deepsleeptime_max = %s,
                    shallowsleeptime_max = %s,
                    waketime_max = %s,
                    remtime_max = %s,
                    created_at = CURRENT_TIMESTAMP
                WHERE id_usuario = %s AND fecha = %s
            """, (
                steps_mean, steps_std, steps_max, steps_sum,
                rr_mean, rr_std, rr_min, rr_max,
                heartrate_mean, heartrate_std, heartrate_min, heartrate_max,
                vfc_mean, vfc_std, vfc_min, vfc_max,
                deepsleeptime_max, shallowsleeptime_max, waketime_max, remtime_max,
                id_usuario, fecha
            ))
            mensaje = "biomarcadores actualizados correctamente"
        else:
            # Insertar nuevo registro
            cursor.execute("""
                INSERT INTO registrobiomark (
                    id_usuario, fecha,
                    steps_mean, steps_std, steps_max, steps_sum,
                    rr_mean, rr_std, rr_min, rr_max,
                    heartrate_mean, heartrate_std, heartrate_min, heartrate_max,
                    vfc_mean, vfc_std, vfc_min, vfc_max,
                    deepsleeptime_max, shallowsleeptime_max, waketime_max, remtime_max
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_usuario, fecha,
                steps_mean, steps_std, steps_max, steps_sum,
                rr_mean, rr_std, rr_min, rr_max,
                heartrate_mean, heartrate_std, heartrate_min, heartrate_max,
                vfc_mean, vfc_std, vfc_min, vfc_max,
                deepsleeptime_max, shallowsleeptime_max, waketime_max, remtime_max
            ))
            mensaje = "biomarcadores guardados correctamente"
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'mensaje': mensaje,
            'success': True
        }), 200
        
    except Exception as e:
        print(f" Error al guardar biomarcadores: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/obtener_biomarcadores_estadisticas/<int:id_usuario>', methods=['GET'])
def obtener_biomarcadores_estadisticas(id_usuario):
    """
    Obtiene las estadísticas de biomarcadores de un usuario desde registrobiomark
    Parámetros opcionales: ?fecha=YYYY-MM-DD o ?dias=30
    """
    try:
        fecha = request.args.get('fecha')
        dias = request.args.get('dias', 30, type=int)
        
        conn = get_connection()
        cursor = get_cursor(conn)
        
        if fecha:
            # Obtener estadísticas de una fecha específica
            cursor.execute("""
                SELECT * FROM registrobiomark 
                WHERE id_usuario = %s AND fecha = %s
                ORDER BY fecha DESC
            """, (id_usuario, fecha))
        else:
            # Obtener estadísticas de los últimos N días
            cursor.execute("""
                SELECT * FROM registrobiomark 
                WHERE id_usuario = %s 
                ORDER BY fecha DESC
                LIMIT %s
            """, (id_usuario, dias))
        
        registros = cursor.fetchall()
        
        # Convertir fechas a string para JSON
        for registro in registros:
            if registro.get('fecha'):
                registro['fecha'] = str(registro['fecha'])
            if registro.get('created_at'):
                registro['created_at'] = str(registro['created_at'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'registros': registros,
            'total': len(registros)
        }), 200
        
    except Exception as e:
        print(f" Error al obtener estadísticas: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/biomarcador_estadisticas_ultimo/<int:id_usuario>', methods=['GET'])
def obtener_ultimas_estadisticas_biomarcador(id_usuario):
    """Obtiene las últimas estadísticas de biomarcadores del usuario"""
    try:
        conn = get_connection()
        cursor = get_cursor(conn)
        
        cursor.execute("""
            SELECT * FROM registrobiomark 
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
            return jsonify({'success': True, 'registro': registro}), 200
        else:
            return jsonify({'success': True, 'registro': None, 'message': 'No hay registros'}), 200
        
    except Exception as e:
        print(f" Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/resumen_estadisticas_usuario/<int:id_usuario>', methods=['GET'])
def resumen_estadisticas_usuario(id_usuario):
    """
    Obtiene un resumen estadístico de todos los registros del usuario
    """
    try:
        conn = get_connection()
        cursor = get_cursor(conn)
        
        # Obtener estadísticas agregadas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registros,
                MIN(fecha) as primera_fecha,
                MAX(fecha) as ultima_fecha,
                AVG(steps_mean) as promedio_steps_mean,
                AVG(steps_sum) as promedio_steps_diarios,
                MAX(steps_max) as max_steps_diarios,
                AVG(heartrate_mean) as promedio_heartrate,
                MIN(heartrate_min) as min_heartrate,
                MAX(heartrate_max) as max_heartrate,
                AVG(vfc_mean) as promedio_vfc,
                AVG(deepsleeptime_max) as promedio_sueno_profundo,
                AVG(shallowsleeptime_max) as promedio_sueno_ligero,
                AVG(remtime_max) as promedio_sueno_rem
            FROM registrobiomark 
            WHERE id_usuario = %s
        """, (id_usuario,))
        
        resumen = cursor.fetchone()
        
        # Obtener últimos 7 días para tendencias
        cursor.execute("""
            SELECT 
                fecha,
                steps_sum,
                heartrate_mean,
                vfc_mean,
                deepsleeptime_max + shallowsleeptime_max + remtime_max as total_sueno
            FROM registrobiomark 
            WHERE id_usuario = %s 
            ORDER BY fecha DESC
            LIMIT 7
        """, (id_usuario,))
        
        tendencias = cursor.fetchall()
        
        # Convertir fechas a string
        if resumen and resumen.get('primera_fecha'):
            resumen['primera_fecha'] = str(resumen['primera_fecha'])
        if resumen and resumen.get('ultima_fecha'):
            resumen['ultima_fecha'] = str(resumen['ultima_fecha'])
        
        for tendencia in tendencias:
            if tendencia.get('fecha'):
                tendencia['fecha'] = str(tendencia['fecha'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'resumen': resumen,
            'tendencias_7dias': tendencias
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


###### BIOMARCADORES LEGACY #######

@app.route('/guardar_biomarcadores', methods=['POST'])
def guardar_biomarcadores_legacy():
    """
    ENDPOINT LEGACY: Mantenido para compatibilidad
    Guarda biomarcadores simples en la tabla biomarcadores_diarios
    """
    try:
        data = request.get_json()
        print(f"📊 Recibiendo biomarcadores (legacy): {data}")
        
        id_usuario = data.get('id_usuario')
        fecha = data.get('fecha')
        pasos = data.get('pasos', 0)
        ritmo_cardiaco = data.get('ritmo_cardiaco')
        sueno_minutos = data.get('sueno_minutos', 0)
        hrv_ms = data.get('hrv_ms', 0.0)
        
        if not id_usuario or not fecha:
            return jsonify({'error': 'id_usuario y fecha son requeridos'}), 400
        
        conn = get_connection()
        cursor = get_cursor(conn)
        
        cursor.execute("SELECT id_usuario FROM usuario WHERE id_usuario = %s", (id_usuario,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        cursor.execute("""
            SELECT id FROM biomarcadores_diarios 
            WHERE id_usuario = %s AND fecha = %s
        """, (id_usuario, fecha))
        
        existe = cursor.fetchone()
        
        if existe:
            cursor.execute("""
                UPDATE biomarcadores_diarios 
                SET pasos = %s, ritmo_cardiaco = %s, sueno_minutos = %s, hrv_ms = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_usuario = %s AND fecha = %s
            """, (pasos, ritmo_cardiaco, sueno_minutos, hrv_ms, id_usuario, fecha))
            mensaje = "Biomarcadores actualizados correctamente"
        else:
            cursor.execute("""
                INSERT INTO biomarcadores_diarios 
                (id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms))
            mensaje = "Biomarcadores guardados correctamente"
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'mensaje': mensaje, 'success': True}), 200
        
    except Exception as e:
        print(f" Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/obtener_biomarcadores/<int:id_usuario>', methods=['GET'])
def obtener_biomarcadores_legacy(id_usuario):
    """
    ENDPOINT LEGACY: Obtiene biomarcadores de la tabla biomarcadores_diarios
    """
    try:
        fecha = request.args.get('fecha')
        dias = request.args.get('dias', 30, type=int)
        
        conn = get_connection()
        cursor = get_cursor(conn)
        
        if fecha:
            cursor.execute("""
                SELECT id, id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms, created_at
                FROM biomarcadores_diarios 
                WHERE id_usuario = %s AND fecha = %s
                ORDER BY fecha DESC
            """, (id_usuario, fecha))
        else:
            cursor.execute("""
                SELECT id, id_usuario, fecha, pasos, ritmo_cardiaco, sueno_minutos, hrv_ms, created_at
                FROM biomarcadores_diarios 
                WHERE id_usuario = %s 
                ORDER BY fecha DESC
                LIMIT %s
            """, (id_usuario, dias))
        
        registros = cursor.fetchall()
        
        for registro in registros:
            if registro.get('fecha'):
                registro['fecha'] = str(registro['fecha'])
            if registro.get('created_at'):
                registro['created_at'] = str(registro['created_at'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'biomarcadores': registros, 'total': len(registros)}), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/biomarcador_ultimo/<int:id_usuario>', methods=['GET'])
def obtener_ultimo_biomarcador_legacy(id_usuario):
    """ENDPOINT LEGACY: Obtiene el último biomarcador de biomarcadores_diarios"""
    try:
        conn = get_connection()
        cursor = get_cursor(conn)
        
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


##### RUTA DE PRUEBA ########

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "Servidor funcionando"}), 200

# LABEL ENCODERS PARA EMOCIONES
# =========================================

# Valores posibles según tus tablas
VALORES_EMOCIONES_GENERALES = [
    "Ninguna", "Éxtasis", "Terror", "Asombro", "Pena", "Odio", "Furia", "Vigilancia", "Admiración"
]

VALORES_EMOCIONES_ESPECIFICAS = [
    "Ninguna", "Alegria", "Serenidad", "Confianza", "Aprobación", "Miedo", "Temor", 
    "Sorpresa", "Distracción", "Tristeza", "Melancolía", "Aversión", "Tedio", 
    "Ira", "Enfado", "Anticipación", "Interés"
]

# Crear y entrenar LabelEncoders
label_encoders = {
    "Emocion Normal predominante": LabelEncoder().fit(VALORES_EMOCIONES_GENERALES),
    "Emocion extraordinaria general": LabelEncoder().fit(VALORES_EMOCIONES_GENERALES),
    "Emocion específica predominante": LabelEncoder().fit(VALORES_EMOCIONES_ESPECIFICAS),
    "Emocion extraordinaria específica": LabelEncoder().fit(VALORES_EMOCIONES_ESPECIFICAS)
}

print("✅ LabelEncoders configurados")

# HADS
PREGUNTAS_ANSIEDAD = [1,3,5,7,9,11,13]
PREGUNTAS_DEPRESION = [2,4,6,8,10,12,14]

# COLUMNAS DEL MODELO
COLUMNAS_MODELO = [
    "steps_mean","steps_std","steps_max","steps_sum",
    "rr_mean","rr_std","rr_min","rr_max",
    "heartrate_mean","heartrate_std","heartrate_min","heartrate_max",
    "vfc_mean","vfc_std","vfc_min","vfc_max",
    "deepsleeptime_max","shallowsleeptime_max","waketime_max","remtime_max",
    "Ansiedad","Depresion",
    "Emocion Normal predominante",
    "Emocion específica predominante",
    "Emocion extraordinaria general",
    "Emocion extraordinaria específica"
]

# =========================================
# FUNCIÓN PARA OBTENER NOMBRE DE EMOCIÓN
# =========================================

def get_emocion_nombre(id_emocion, tipo):
    """Obtiene el nombre de la emoción desde la BD"""
    if not id_emocion or id_emocion == 0:
        return "Ninguna"
    
    try:
        conn = get_connection()
        cursor = get_cursor(conn)
        
        if tipo == "general":
            cursor.execute("SELECT emocion FROM emocionescat WHERE id_emocion = %s", (id_emocion,))
        else:
            cursor.execute("SELECT emocion FROM emocion_espe WHERE id_espe = %s", (id_emocion,))
        
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return resultado['emocion'] if resultado else "Ninguna"
    except:
        return "Ninguna"

# =========================================
# ENDPOINT DE PREDICCIÓN
# =========================================

@app.route('/prediccion/<int:id_usuario>', methods=['GET'])
def prediccion_usuario(id_usuario):
    try:
        if modelo is None:
            return jsonify({"success": False, "error": "Modelo no cargado"}), 500
        
        conn = get_connection()
        cursor = get_cursor(conn)
        
        # 1. BIOMARCADORES
        cursor.execute("""
            SELECT *
            FROM registrobiomark
            WHERE id_usuario = %s
            ORDER BY fecha DESC
            LIMIT 1
        """, (id_usuario,))
        
        biomark = cursor.fetchone()
        
        if not biomark:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "No hay biomarcadores"}), 404
        
        # 2. HADS
        ansiedad = 0
        depresion = 0
        
        cursor.execute("""
            SELECT id_evaluacion
            FROM evaluacion
            WHERE id_usuario = %s AND tipo_evaluacion = 'HADS'
            ORDER BY fecha DESC, id_evaluacion DESC
            LIMIT 1
        """, (id_usuario,))
        
        eval_hads = cursor.fetchone()
        
        if eval_hads:
            cursor.execute("""
                SELECT id_pregunta, puntaje
                FROM respuestas_usuario_hads
                WHERE id_evaluacion = %s
            """, (eval_hads['id_evaluacion'],))
            
            respuestas = cursor.fetchall()
            
            for r in respuestas:
                pregunta = r['id_pregunta']
                puntaje = r['puntaje']
                if pregunta in PREGUNTAS_ANSIEDAD:
                    ansiedad += puntaje
                elif pregunta in PREGUNTAS_DEPRESION:
                    depresion += puntaje
        
        # 3. EMOCIONES (obtener IDs)
        cursor.execute("""
            SELECT id_emocion_general, id_emocion_especifica, tipo_registro
            FROM registro_emociones_usuario
            WHERE id_usuario = %s
            ORDER BY id_registro DESC
            LIMIT 1
        """, (id_usuario,))
        
        emocion = cursor.fetchone()
        
        id_general = 0
        id_especifica = 0
        tipo_registro = "predominante"
        
        if emocion:
            id_general = emocion.get('id_emocion_general') or 0
            id_especifica = emocion.get('id_emocion_especifica') or 0
            tipo_registro = emocion.get('tipo_registro', 'predominante')
        
        cursor.close()
        conn.close()
        
        # 4. Obtener NOMBRES de las emociones
        nombre_general = get_emocion_nombre(id_general, "general")
        nombre_especifica = get_emocion_nombre(id_especifica, "especifica")
        
        print(f"📊 Emociones - General: {nombre_general} (ID:{id_general}), Específica: {nombre_especifica} (ID:{id_especifica})")
        
        # 5. CONSTRUIR INPUT
        data_modelo = {
            "steps_mean": float(biomark.get('steps_mean', 0)),
            "steps_std": float(biomark.get('steps_std', 0)),
            "steps_max": int(biomark.get('steps_max', 0)),
            "steps_sum": int(biomark.get('steps_sum', 0)),
            "rr_mean": float(biomark.get('rr_mean', 0)),
            "rr_std": float(biomark.get('rr_std', 0)),
            "rr_min": int(biomark.get('rr_min', 0)),
            "rr_max": int(biomark.get('rr_max', 0)),
            "heartrate_mean": float(biomark.get('heartrate_mean', 0)),
            "heartrate_std": float(biomark.get('heartrate_std', 0)),
            "heartrate_min": int(biomark.get('heartrate_min', 0)),
            "heartrate_max": int(biomark.get('heartrate_max', 0)),
            "vfc_mean": float(biomark.get('vfc_mean', 0)),
            "vfc_std": float(biomark.get('vfc_std', 0)),
            "vfc_min": int(biomark.get('vfc_min', 0)),
            "vfc_max": int(biomark.get('vfc_max', 0)),
            "deepsleeptime_max": float(biomark.get('deepsleeptime_max', 0)),
            "shallowsleeptime_max": float(biomark.get('shallowsleeptime_max', 0)),
            "waketime_max": float(biomark.get('waketime_max', 0)),
            "remtime_max": float(biomark.get('remtime_max', 0)),
            "Ansiedad": ansiedad,
            "Depresion": depresion
        }
        
        # Asignar emociones según tipo (usando NOMBRES)
        if tipo_registro == "predominante":
            data_modelo["Emocion Normal predominante"] = nombre_general
            data_modelo["Emocion específica predominante"] = nombre_especifica
            data_modelo["Emocion extraordinaria general"] = "Ninguna"
            data_modelo["Emocion extraordinaria específica"] = "Ninguna"
        else:  # extraordinaria
            data_modelo["Emocion Normal predominante"] = "Ninguna"
            data_modelo["Emocion específica predominante"] = "Ninguna"
            data_modelo["Emocion extraordinaria general"] = nombre_general
            data_modelo["Emocion extraordinaria específica"] = nombre_especifica
        
        # 6. CONVERTIR NOMBRES A NÚMEROS CON LABELENCODER
        for col in ["Emocion Normal predominante", "Emocion específica predominante", 
                    "Emocion extraordinaria general", "Emocion extraordinaria específica"]:
            valor_texto = data_modelo[col]
            try:
                data_modelo[col] = int(label_encoders[col].transform([valor_texto])[0])
            except:
                # Si la emoción no está en el encoder, usar "Ninguna" (índice 0)
                data_modelo[col] = 0
                print(f"⚠️ Emoción no reconocida: {valor_texto}")
        
        # 7. PREDICCIÓN
        df = pd.DataFrame([data_modelo])
        
        # Asegurar todas las columnas
        for col in COLUMNAS_MODELO:
            if col not in df.columns:
                df[col] = 0
        
        df = df[COLUMNAS_MODELO]
        df = df.astype(float)
        
        pred = modelo.predict(df)
        proba = modelo.predict_proba(df)
        
        return jsonify({
            "success": True,
            "prediccion": int(pred[0]),
            "probabilidad_sin_riesgo": float(proba[0][0]),
            "probabilidad_con_riesgo": float(proba[0][1]),
            "ansiedad": ansiedad,
            "depresion": depresion,
            "emocion_general": nombre_general,
            "emocion_especifica": nombre_especifica,
            "tipo_emocion": tipo_registro,
            "debug_valores_numericos": {
                "Emocion Normal predominante": data_modelo["Emocion Normal predominante"],
                "Emocion específica predominante": data_modelo["Emocion específica predominante"],
                "Emocion extraordinaria general": data_modelo["Emocion extraordinaria general"],
                "Emocion extraordinaria específica": data_modelo["Emocion extraordinaria específica"]
            }
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# =========================================
# ENDPOINTS DE PRUEBA
# =========================================

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "Servidor funcionando"})

@app.route('/estado', methods=['GET'])
def estado():
    return jsonify({
        "success": True,
        "servidor": "activo",
        "modelo_cargado": modelo is not None
    })

@app.route('/emociones_disponibles', methods=['GET'])
def emociones_disponibles():
    """Ver qué emociones reconoce el LabelEncoder"""
    return jsonify({
        "emociones_generales": VALORES_EMOCIONES_GENERALES,
        "emociones_especificas": VALORES_EMOCIONES_ESPECIFICAS,
        "mapeo_normal_predominante": dict(zip(
            VALORES_EMOCIONES_GENERALES,
            label_encoders["Emocion Normal predominante"].transform(VALORES_EMOCIONES_GENERALES).tolist()
        ))
    })
######### MANEJO DE ERRORES #####

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
        print("\n📊 ENDPOINTS BIOMARCADORES (NUEVOS):")
        print("   POST /guardar_biomarcadores_estadisticas")
        print("   GET  /obtener_biomarcadores_estadisticas/<id>")
        print("   GET  /biomarcador_estadisticas_ultimo/<id>")
        print("   GET  /resumen_estadisticas_usuario/<id>")
        print("\n📊 ENDPOINTS BIOMARCADORES (LEGACY):")
        print("   POST /guardar_biomarcadores")
        print("   GET  /obtener_biomarcadores/<id>")
        print("   GET  /biomarcador_ultimo/<id>")
        print("   GET  /prediccion/<id>")
        print("="*50 + "\n")
        
        app.run(host='0.0.0.0', port=5000, debug=True)
