from db.BD import get_connection, get_cursor
from datetime import datetime, date, timedelta

class EvaluacionModel:
    """Modelo para manejar evaluaciones"""
    
    @staticmethod
    def obtener_preguntas_hads():
        """Obtener todas las preguntas HADS con sus opciones de respuesta"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            cursor.execute("""
                SELECT p.id_pregunta, p.pregunta as texto, p.tipo as categoria,
                       r.id_respuesta, r.opcion as respuesta_texto, r.puntaje
                FROM preguntas_hads p
                LEFT JOIN respuestas_hads r ON p.id_pregunta = r.id_pregunta
                ORDER BY p.id_pregunta, r.puntaje
            """)
            
            resultados = cursor.fetchall()
            
            preguntas = {}
            for row in resultados:
                id_pregunta = row['id_pregunta']
                if id_pregunta not in preguntas:
                    preguntas[id_pregunta] = {
                        'id_pregunta': id_pregunta,
                        'texto': row['texto'],
                        'categoria': row['categoria'],
                        'respuestas': []
                    }
                if row['id_respuesta']:
                    preguntas[id_pregunta]['respuestas'].append({
                        'id_respuesta': row['id_respuesta'],
                        'texto': row['respuesta_texto'],
                        'puntaje': row['puntaje']
                    })
            
            cursor.close()
            conn.close()
            return list(preguntas.values())
        except Exception as e:
            print(f"❌ Error en obtener_preguntas_hads: {str(e)}")
            return []
    
    @staticmethod
    def obtener_preguntas_ders():
        """Obtener todas las preguntas DERS con sus opciones de respuesta"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            cursor.execute("""
                SELECT p.id_pregunta, p.pregunta as texto, p.tipo as categoria,
                       r.id_respuesta, r.opcion as respuesta_texto, r.puntaje
                FROM preguntas_ders p
                LEFT JOIN respuestas_ders r ON p.id_pregunta = r.id_pregunta
                ORDER BY p.id_pregunta, r.puntaje
            """)
            
            resultados = cursor.fetchall()
            
            preguntas = {}
            for row in resultados:
                id_pregunta = row['id_pregunta']
                if id_pregunta not in preguntas:
                    preguntas[id_pregunta] = {
                        'id_pregunta': id_pregunta,
                        'texto': row['texto'],
                        'categoria': row['categoria'],
                        'respuestas': []
                    }
                if row['id_respuesta']:
                    preguntas[id_pregunta]['respuestas'].append({
                        'id_respuesta': row['id_respuesta'],
                        'texto': row['respuesta_texto'],
                        'puntaje': row['puntaje']
                    })
            
            cursor.close()
            conn.close()
            return list(preguntas.values())
        except Exception as e:
            print(f"❌ Error en obtener_preguntas_ders: {str(e)}")
            return []
    
    @staticmethod
    def puede_responder_hads(id_usuario):
        """Verifica si el usuario puede responder HADS (cada 30 días)"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            cursor.execute("""
                SELECT fecha 
                FROM evaluacion 
                WHERE id_usuario = %s AND tipo_evaluacion = 'HADS'
                ORDER BY fecha DESC 
                LIMIT 1
            """, (id_usuario,))
            
            ultima = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not ultima:
                return True, "Puede realizar la evaluación HADS"
            
            ultima_fecha = ultima['fecha']
            hoy = date.today()
            dias_diferencia = (hoy - ultima_fecha).days
            
            if dias_diferencia >= 30:
                return True, f"Puede realizar la evaluación (última fue hace {dias_diferencia} días)"
            else:
                dias_restantes = 30 - dias_diferencia
                return False, f"Debe esperar {dias_restantes} días para volver a realizar HADS"
        except Exception as e:
            print(f"❌ Error en puede_responder_hads: {str(e)}")
            return False, "Error al verificar disponibilidad"
    
    @staticmethod
    def puede_responder_ders(id_usuario):
        """Verifica si el usuario puede responder DERS (una vez por día)"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            cursor.execute("""
                SELECT fecha 
                FROM evaluacion 
                WHERE id_usuario = %s AND tipo_evaluacion = 'DERS'
                ORDER BY fecha DESC 
                LIMIT 1
            """, (id_usuario,))
            
            ultima = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not ultima:
                return True, "Puede realizar la evaluación DERS"
            
            ultima_fecha = ultima['fecha']
            hoy = date.today()
            
            if ultima_fecha == hoy:
                return False, "Ya realizó DERS hoy. Puede volver a responder mañana"
            else:
                return True, "Puede realizar la evaluación DERS"
        except Exception as e:
            print(f"❌ Error en puede_responder_ders: {str(e)}")
            return False, "Error al verificar disponibilidad"
    
    @staticmethod
    def crear_evaluacion(id_usuario, tipo_evaluacion):
        """Crear una nueva evaluación"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            fecha_actual = date.today()
            cursor.execute("""
                INSERT INTO evaluacion (id_usuario, tipo_evaluacion, fecha, puntaje_total)
                VALUES (%s, %s, %s, %s)
                RETURNING id_evaluacion
            """, (id_usuario, tipo_evaluacion, fecha_actual, 0))
            
            id_evaluacion = cursor.fetchone()['id_evaluacion']  
            conn.commit()
            cursor.close()
            conn.close()
            return True, id_evaluacion
        except Exception as e:
            print(f"❌ Error en crear_evaluacion: {str(e)}")
            return False, None
    
    @staticmethod
    def guardar_respuestas_hads(id_evaluacion, respuestas):
        """Guardar respuestas de evaluación HADS"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            puntaje_total = 0
            for respuesta in respuestas:
                id_pregunta = respuesta.get('id_pregunta')
                id_respuesta = respuesta.get('id_respuesta')
                puntaje = respuesta.get('puntaje', 0)
                
                cursor.execute("""
                    INSERT INTO respuestas_usuario_hads 
                    (id_evaluacion, id_pregunta, id_respuesta, puntaje)
                    VALUES (%s, %s, %s, %s)
                """, (id_evaluacion, id_pregunta, id_respuesta, puntaje))
                puntaje_total += puntaje
            
            cursor.execute("""
                UPDATE evaluacion SET puntaje_total = %s WHERE id_evaluacion = %s
            """, (puntaje_total, id_evaluacion))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True, puntaje_total
        except Exception as e:
            print(f"❌ Error en guardar_respuestas_hads: {str(e)}")
            return False, None
    
    @staticmethod
    def guardar_respuestas_ders(id_evaluacion, respuestas):
        """Guardar respuestas de evaluación DERS"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            puntaje_total = 0
            for respuesta in respuestas:
                id_pregunta = respuesta.get('id_pregunta')
                id_respuesta = respuesta.get('id_respuesta')
                puntaje = respuesta.get('puntaje', 0)
                
                cursor.execute("""
                    INSERT INTO respuestas_usuario_ders 
                    (id_evaluacion, id_pregunta, id_respuesta, puntaje)
                    VALUES (%s, %s, %s, %s)
                """, (id_evaluacion, id_pregunta, id_respuesta, puntaje))
                puntaje_total += puntaje
            
            cursor.execute("""
                UPDATE evaluacion SET puntaje_total = %s WHERE id_evaluacion = %s
            """, (puntaje_total, id_evaluacion))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True, puntaje_total
        except Exception as e:
            print(f"❌ Error en guardar_respuestas_ders: {str(e)}")
            return False, None
    
    @staticmethod
    def obtener_evaluaciones_usuario(id_usuario):
        """Obtener todas las evaluaciones de un usuario"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            cursor.execute("""
                SELECT id_evaluacion, tipo_evaluacion, fecha, puntaje_total
                FROM evaluacion
                WHERE id_usuario = %s
                ORDER BY fecha DESC
            """, (id_usuario,))
            
            evaluaciones = cursor.fetchall()
            cursor.close()
            conn.close()
            return evaluaciones
        except Exception as e:
            print(f"❌ Error en obtener_evaluaciones_usuario: {str(e)}")
            return []
    
    @staticmethod
    def obtener_detalle_hads(id_evaluacion):
        """Obtener detalle de evaluación HADS"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  # ✅ CORREGIDO
            
            cursor.execute("""
                SELECT ru.id_pregunta, ru.id_respuesta, ru.puntaje,
                       p.pregunta as pregunta_texto, p.tipo as categoria,
                       r.opcion as respuesta_texto
                FROM respuestas_usuario_hads ru
                JOIN preguntas_hads p ON ru.id_pregunta = p.id_pregunta
                JOIN respuestas_hads r ON ru.id_respuesta = r.id_respuesta
                WHERE ru.id_evaluacion = %s
                ORDER BY ru.id_pregunta
            """, (id_evaluacion,))
            
            respuestas = cursor.fetchall()
            cursor.close()
            conn.close()
            
            puntaje_ansiedad = 0
            puntaje_depresion = 0
            
            for r in respuestas:
                categoria = r['categoria'].lower() if r['categoria'] else ''
                if 'ansiedad' in categoria:
                    puntaje_ansiedad += r['puntaje']
                elif 'depresion' in categoria:
                    puntaje_depresion += r['puntaje']
            
            return respuestas, puntaje_ansiedad, puntaje_depresion
        except Exception as e:
            print(f"❌ Error en obtener_detalle_hads: {str(e)}")
            return [], 0, 0
    
    @staticmethod
    def obtener_detalle_ders(id_evaluacion):
        """Obtener detalle de evaluación DERS"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            cursor.execute("""
                SELECT ru.id_pregunta, ru.id_respuesta, ru.puntaje,
                       p.pregunta as pregunta_texto, p.tipo as categoria,
                       r.opcion as respuesta_texto
                FROM respuestas_usuario_ders ru
                JOIN preguntas_ders p ON ru.id_pregunta = p.id_pregunta
                JOIN respuestas_ders r ON ru.id_respuesta = r.id_respuesta
                WHERE ru.id_evaluacion = %s
                ORDER BY ru.id_pregunta
            """, (id_evaluacion,))
            
            respuestas = cursor.fetchall()
            cursor.close()
            conn.close()
            
            categorias = {
                'claridad': 0,
                'atencion': 0,
                'descontrol': 0,
                'rechazo': 0,
                'interferencia': 0,
                'estrategias': 0
            }
            
            mapeo = {
                'Claridad': 'claridad',
                'Conciencia': 'atencion',
                'Impulsos': 'descontrol',
                'No aceptación': 'rechazo',
                'Objetivos': 'interferencia',
                'Estrategias': 'estrategias'
            }
            
            for r in respuestas:
                cat = r['categoria'] if r['categoria'] else ''
                cat_normalizada = mapeo.get(cat, cat.lower())
                if cat_normalizada in categorias:
                    categorias[cat_normalizada] += r['puntaje']
            
            return respuestas, categorias
        except Exception as e:
            print(f"❌ Error en obtener_detalle_ders: {str(e)}")
            return [], {}
    
    @staticmethod
    def obtener_emociones():
        """Obtener todas las emociones generales y específicas"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            cursor.execute("SELECT id_emocion, emocion FROM emocionescat ORDER BY id_emocion")
            emociones_generales = cursor.fetchall()
            
            cursor.execute("SELECT id_espe, id_emocion, emocion FROM emocion_espe ORDER BY id_emocion, id_espe")
            emociones_especificas = cursor.fetchall()
            
            cursor.close()
            conn.close()
            return emociones_generales, emociones_especificas
        except Exception as e:
            print(f"❌ Error en obtener_emociones: {str(e)}")
            return [], []
    
    @staticmethod
    def registrar_emocion(id_usuario, id_emocion_general, id_emocion_especifica, tipo_registro, momento, fecha, comentario=None):
        """Registrar una emoción del usuario"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            cursor.execute("""
                INSERT INTO registro_emociones_usuario 
                (id_usuario, id_emocion_general, id_emocion_especifica, tipo_registro, momento, fecha, comentario)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_registro
            """, (id_usuario, id_emocion_general, id_emocion_especifica, tipo_registro, momento, fecha, comentario))
            
            id_registro = cursor.fetchone()['id_registro']
            conn.commit()
            cursor.close()
            conn.close()
            return True, id_registro
        except Exception as e:
            print(f"❌ Error en registrar_emocion: {str(e)}")
            return False, None