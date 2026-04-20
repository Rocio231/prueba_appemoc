from flask import jsonify, request
from modelo.evaluacion_model import EvaluacionModel
from db.BD import get_connection, get_cursor
import traceback
from datetime import date, timedelta

class EvaluacionController:
    """Controlador para gestión de evaluaciones"""
    
    @staticmethod
    def obtener_preguntas_hads():
        try:
            preguntas = EvaluacionModel.obtener_preguntas_hads()
            if not preguntas:
                return jsonify({"success": False, "message": "No hay preguntas HADS"}), 404
            return jsonify({"success": True, "preguntas": preguntas}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def obtener_preguntas_ders():
        try:
            preguntas = EvaluacionModel.obtener_preguntas_ders()
            if not preguntas:
                return jsonify({"success": False, "message": "No hay preguntas DERS"}), 404
            return jsonify({"success": True, "preguntas": preguntas}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def verificar_hads():
        try:
            data = request.json
            id_usuario = data.get('id_usuario')
            if not id_usuario:
                return jsonify({"success": False, "message": "ID de usuario requerido"}), 400
            puede, mensaje = EvaluacionModel.puede_responder_hads(id_usuario)
            return jsonify({"success": True, "puede_responder": puede, "mensaje": mensaje}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def verificar_ders():
        try:
            data = request.json
            id_usuario = data.get('id_usuario')
            if not id_usuario:
                return jsonify({"success": False, "message": "ID de usuario requerido"}), 400
            puede, mensaje = EvaluacionModel.puede_responder_ders(id_usuario)
            return jsonify({"success": True, "puede_responder": puede, "mensaje": mensaje}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def crear_evaluacion():
        try:
            data = request.json
            id_usuario = data.get('id_usuario')
            tipo = data.get('tipo', 'HADS')
            
            if not id_usuario:
                return jsonify({"success": False, "message": "ID de usuario requerido"}), 400
            
            if tipo == 'HADS':
                puede, mensaje = EvaluacionModel.puede_responder_hads(id_usuario)
            else:
                puede, mensaje = EvaluacionModel.puede_responder_ders(id_usuario)
            
            if not puede:
                return jsonify({"success": False, "message": mensaje}), 400
            
            success, id_evaluacion = EvaluacionModel.crear_evaluacion(id_usuario, tipo)
            
            if success:
                return jsonify({
                    "success": True,
                    "id_evaluacion": id_evaluacion,
                    "message": f"Evaluación {tipo} creada"
                }), 201
            else:
                return jsonify({"success": False, "message": "Error al crear evaluación"}), 500
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def guardar_respuestas():
        try:
            data = request.json
            id_evaluacion = data.get('id_evaluacion')
            respuestas = data.get('respuestas')
            tipo = data.get('tipo', 'HADS')
            
            if not id_evaluacion:
                return jsonify({"success": False, "message": "ID de evaluación requerido"}), 400
            if not respuestas:
                return jsonify({"success": False, "message": "Respuestas requeridas"}), 400
            
            conn = get_connection()
            cursor = get_cursor(conn)  # ✅ CORREGIDO
            
            cursor.execute("SELECT tipo_evaluacion FROM evaluacion WHERE id_evaluacion = %s", (id_evaluacion,))
            eval_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            tipo_real = eval_data['tipo_evaluacion'] if eval_data else tipo
            
            if tipo_real == 'HADS':
                success, puntaje_total = EvaluacionModel.guardar_respuestas_hads(id_evaluacion, respuestas)
            else:
                success, puntaje_total = EvaluacionModel.guardar_respuestas_ders(id_evaluacion, respuestas)
            
            if success:
                return jsonify({
                    "success": True,
                    "puntaje_total": puntaje_total,
                    "message": "Respuestas guardadas"
                }), 200
            else:
                return jsonify({"success": False, "message": "Error al guardar respuestas"}), 500
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def obtener_evaluaciones_usuario(id_usuario):
        try:
            evaluaciones = EvaluacionModel.obtener_evaluaciones_usuario(id_usuario)
            return jsonify({"success": True, "evaluaciones": evaluaciones}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def obtener_detalle_hads(id_evaluacion):
        try:
            respuestas, ansiedad, depresion = EvaluacionModel.obtener_detalle_hads(id_evaluacion)
            return jsonify({
                "success": True,
                "respuestas": respuestas,
                "puntaje_ansiedad": ansiedad,
                "puntaje_depresion": depresion
            }), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def obtener_detalle_ders(id_evaluacion):
        try:
            respuestas, categorias = EvaluacionModel.obtener_detalle_ders(id_evaluacion)
            return jsonify({
                "success": True,
                "respuestas": respuestas,
                "puntajes_categoria": categorias
            }), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def obtener_emociones():
        try:
            emociones_generales, emociones_especificas = EvaluacionModel.obtener_emociones()
            return jsonify({
                "success": True,
                "emociones_generales": emociones_generales,
                "emociones_especificas": emociones_especificas
            }), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def registrar_emocion():
        try:
            data = request.json
            id_usuario = data.get('id_usuario')
            id_emocion_general = data.get('id_emocion_general')
            id_emocion_especifica = data.get('id_emocion_especifica')
            tipo_registro = data.get('tipo_registro')
            momento = data.get('momento')
            fecha = data.get('fecha')
            comentario = data.get('comentario')
            
            if not all([id_usuario, id_emocion_general, id_emocion_especifica, tipo_registro, momento, fecha]):
                return jsonify({"success": False, "message": "Datos incompletos"}), 400
            
            success, id_registro = EvaluacionModel.registrar_emocion(
                id_usuario, id_emocion_general, id_emocion_especifica,
                tipo_registro, momento, fecha, comentario
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "id_registro": id_registro,
                    "message": "Emoción registrada correctamente"
                }), 201
            else:
                return jsonify({"success": False, "message": "Error al registrar emoción"}), 500
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def test_emociones(id_usuario, dias=30):
        """Método de prueba para verificar que el controlador funciona"""
        return jsonify({
            "success": True,
            "message": f"Método funcionando para usuario {id_usuario} con {dias} días",
            "test_data": [
                {"emocionGeneral": "Alegría", "emocionEspecifica": "Éxtasis", "tipo": "predominante"}
            ]
        })
    
    @staticmethod
    @staticmethod
def obtener_registros_emociones(id_usuario, dias=30):
    """Obtener registros de emociones de un usuario"""
    try:
        if isinstance(dias, str):
            dias = int(dias)
        
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
                COALESCE(ec.emocion, 'Sin emoción') as emocionGeneral,
                COALESCE(ee.emocion, 'Sin emoción específica') as emocionEspecifica
            FROM registro_emociones_usuario re
            LEFT JOIN emocionescat ec ON re.id_emocion_general = ec.id_emocion
            LEFT JOIN emocion_espe ee ON re.id_emocion_especifica = ee.id_espe
            WHERE re.id_usuario = %s AND re.fecha >= %s
            ORDER BY re.fecha DESC
        """, (id_usuario, fecha_limite))
        
        registros = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for registro in registros:
            if registro.get('fecha'):
                registro['fecha'] = str(registro['fecha'])
            # Asegurar que nunca sean null
            if registro.get('emocionGeneral') is None:
                registro['emocionGeneral'] = 'Sin emoción'
            if registro.get('emocionEspecifica') is None:
                registro['emocionEspecifica'] = 'Sin especificar'
        
        return jsonify({
            "success": True,
            "registros": registros
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
        
        
        
        
