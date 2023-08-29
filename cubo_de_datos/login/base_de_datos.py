## import psycopg2
import os
import sqlite3

##directorio de ejecucion 
current_directory = os.getcwd()
file_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_directory)
new_current_directory = os.getcwd()



# Conectar a la base de datos (se creará si no existe)
conn = sqlite3.connect('usuarios.db')

# Crear un cursor para ejecutar comandos SQL
cursor = conn.cursor()

## tablas del modelo
# Definir la tabla de usuarios
cursor.execute('''
    CREATE TABLE user (
        id INTEGER PRIMARY KEY,
        nombre TEXT,
        password INTEGER
    )
''')

# Definir la tabla de registros
cursor.execute('''
    CREATE TABLE registro (
        id INTEGER PRIMARY KEY,
        contador INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE profile (
        id INTEGER PRIMARY KEY,
        contador INTEGER
    )
''')

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()
