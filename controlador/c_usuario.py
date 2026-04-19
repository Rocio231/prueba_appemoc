from flask import jsonify, request
from modelo.usuario import UsuarioModel
from db.BD import hash_password
import re
import traceback

class UsuarioController:
    """Controlador para gestión de usuarios"""
    
    @staticmethod
    def login():
        """Manejar solicitud de login"""
        try:
            if not request.is_json:
                return jsonify({"success": False, "message": "Se esperaba JSON"}), 400
            
            data = request.json
            correo = data.get('correo')
            contraseña = data.get('contraseña')
            
            if not contraseña:
                contraseña = data.get('contrasena')
            if not contraseña:
                contraseña = data.get('password')
            
            if not correo or not contraseña:
                return jsonify({"success": False, "message": "Correo y contraseña son obligatorios"}), 400
            
            correo_normalizado = correo.lower()
            user = UsuarioModel.find_by_email(correo_normalizado)
            
            if not user:
                return jsonify({"success": False, "message": "Correo incorrecto"}), 401
            
            hashed_password = hash_password(contraseña)
            
            if user['contraseña'] != hashed_password:
                return jsonify({"success": False, "message": "Contraseña incorrecta"}), 401
            
            return jsonify({
                "success": True,
                "id_usuario": user['id_usuario'],
                "nombre": user['nombre'],
                "message": "Login exitoso"
            })
            
        except Exception as e:
            print(f"❌ Error en login: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    @staticmethod
    def register():
        """Manejar solicitud de registro"""
        try:
            if not request.is_json:
                return jsonify({"success": False, "message": "Se esperaba JSON"}), 400
            
            data = request.json
            correo = data.get('correo')
            contraseña = data.get('contraseña')
            if not contraseña:
                contraseña = data.get('contrasena')
            if not contraseña:
                contraseña = data.get('password')
            
            nombre = data.get('nombre')
            edad = data.get('edad')
            genero = data.get('genero')
            
            # Limpiar nombre
            nombre = nombre.split('\n')[0].strip() if nombre else "Usuario"
            if not nombre or len(nombre) < 2:
                nombre = "Usuario"
            
            if not correo:
                return jsonify({"success": False, "message": "El correo es obligatorio"}), 400
            if not contraseña:
                return jsonify({"success": False, "message": "La contraseña es obligatoria"}), 400
            if not nombre:
                return jsonify({"success": False, "message": "El nombre es obligatorio"}), 400
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, correo):
                return jsonify({"success": False, "message": "Formato de correo no válido"}), 400
            
            if len(contraseña) < 6:
                return jsonify({"success": False, "message": "La contraseña debe tener al menos 6 caracteres"}), 400
            
            correo_normalizado = correo.lower()
            
            existing_user = UsuarioModel.find_by_email(correo_normalizado)
            if existing_user:
                return jsonify({"success": False, "message": "El correo ya está registrado"}), 400
            
            hashed_password = hash_password(contraseña)
            success, user_id = UsuarioModel.create_user(
                correo=correo_normalizado,
                contraseña=hashed_password,
                nombre=nombre,
                edad=edad if edad else None,
                genero=genero if genero else None
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "id_usuario": user_id,
                    "message": "Usuario registrado exitosamente"
                }), 201
            else:
                return jsonify({"success": False, "message": "Error al crear usuario"}), 400
                
        except Exception as e:
            print(f"❌ Error en registro: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500