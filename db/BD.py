import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import hashlib


load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db.lmagukxxlzodpsjdbknl.supabase.co'),
        dbname=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD'),  # se agrega en reander
        port=os.getenv('DB_PORT', '5432')
    )

def get_cursor(conn):
    """Cursor tipo diccionario (como dictionary=True en MySQL)"""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def hash_password(password):
    """Encriptar contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()