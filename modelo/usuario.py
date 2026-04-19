from db.BD import get_connection, get_cursor
from datetime import datetime

class UsuarioModel:
    """Modelo para manejar operaciones de usuario"""
    
    @staticmethod
    def find_by_email(email):
        """Buscar usuario por correo"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            cursor.execute("""
                SELECT id_usuario, correo, nombre, contraseña, edad, genero
                FROM usuario
                WHERE correo = %s
            """, (email,))
            
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            print(f"❌ Error en find_by_email: {str(e)}")
            return None
    
    @staticmethod
    def find_by_id(user_id):
        """Buscar usuario por ID"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn) 
            
            cursor.execute("""
                SELECT id_usuario, correo, nombre, edad, genero
                FROM usuario
                WHERE id_usuario = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            print(f"❌ Error en find_by_id: {str(e)}")
            return None
    
    @staticmethod
    def create_user(correo, contraseña, nombre, edad=None, genero=None):
        """Crear nuevo usuario"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn) 
            
            cursor.execute("""
                INSERT INTO usuario (correo, contraseña, nombre, edad, genero)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_usuario
            """, (correo, contraseña, nombre, edad, genero))
            
            
            user_id = cursor.fetchone()['id_usuario']
            conn.commit()
            cursor.close()
            conn.close()
            return True, user_id
        except Exception as e:
            print(f"❌ Error SQL: {str(e)}")
            return False, None
    
    @staticmethod
    def existe_usuario(correo):
        """Verificar si un usuario existe"""
        try:
            conn = get_connection()
            cursor = get_cursor(conn)  
            
            cursor.execute("SELECT id_usuario FROM usuario WHERE correo = %s", (correo,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"❌ Error en existe_usuario: {str(e)}")
            return False