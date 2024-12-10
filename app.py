from bson import ObjectId
from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from flask import request, jsonify
import datetime
import jwt
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuración de la conexión a MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI","mongodb+srv://pepelopez7:w6AhUgzBS07j5Imc@plsmotors.ctzkm.mongodb.net/?retryWrites=true&w=majority&appName=PLSMotors")
client = MongoClient(MONGO_URI)
db = client['db_plsmotors']

app.config['SECRET_KEY'] = 'abc123xyz456'

# Colecciones
vehiculos_collection = db['vehiculos']
publicaciones_collection = db['publicaciones']
usuarios_collection = db['usuarios']
favoritos_collection = db['favoritos']


# TOKEN

def requiere_token(func):
    @wraps(func)
    def verificacion_token(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'El token ha caducado o no se ha introducido.'}), 401

        token = auth_header.split(' ')[1]

        try:
            decoded_token = jwt.decode(token, 'abc123xyz456', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'El token ha expirado.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido.'}), 401

        return func(*args, **kwargs)

    return verificacion_token


# IMÁGENES

UPLOAD_FOLDER = os.path.join('static', 'imagenes')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear la carpeta si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Ruta para subir una imagen
@app.route('/subir_imagen', methods=['POST'])
@requiere_token
def subir_imagen():
    if 'imagen' not in request.files:
        return jsonify({'error': 'No se encontró ningún archivo'}), 400

    archivos = request.files.getlist('imagen')  # Soporte para múltiples imágenes
    rutas_guardadas = []

    for archivo in archivos:
        if archivo.filename == '':
            return jsonify({'error': 'El archivo no tiene nombre'}), 400

        # Validar que sea un archivo permitido
        if archivo and archivo.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            # Asegurar el nombre del archivo
            nombre_seguro = secure_filename(archivo.filename)
            ruta_guardada = os.path.join(app.config['UPLOAD_FOLDER'], nombre_seguro)

            # Guardar el archivo
            archivo.save(ruta_guardada)
            rutas_guardadas.append(ruta_guardada)
        else:
            return jsonify({'error': f'El archivo {archivo.filename} no es válido'}), 400

    return jsonify({'mensaje': 'Imágenes subidas con éxito', 'rutas': rutas_guardadas}), 200


# Ruta para eliminar una imagen
@app.route('/eliminar_imagenes', methods=['POST'])
@requiere_token
def eliminar_imagenes():
    datos = request.get_json()

    if not datos or 'imagenes' not in datos:
        return jsonify({'error': 'No se proporcionaron imágenes para eliminar'}), 400

    imagenes = datos['imagenes']
    errores = []

    for imagen in imagenes:
        # Extraer solo el nombre del archivo eliminando la ruta completa
        nombre_imagen = os.path.basename(imagen)
        ruta_imagen = os.path.join(app.config['UPLOAD_FOLDER'], nombre_imagen)

        if os.path.exists(ruta_imagen):
            try:
                os.remove(ruta_imagen)
            except Exception as e:
                errores.append({'imagen': nombre_imagen, 'error': str(e)})
        else:
            errores.append({'imagen': nombre_imagen, 'error': 'No encontrada'})

    if errores:
        return jsonify({'mensaje': 'Algunas imágenes no se pudieron eliminar', 'errores': errores}), 207
    return jsonify({'mensaje': 'Todas las imágenes fueron eliminadas con éxito'}), 200


# VEHÍCULOS

# Obtener todos los vehículos
@app.route('/vehiculos', methods=['GET'])
def obtener_vehiculos():
    # Obtenemos los filtros de los parámetros de consulta
    filtros = {}

    # Marca y modelo
    marca = request.args.get('brand')
    if marca and marca != "all":
        filtros['marca'] = marca

    modelo = request.args.get('model')
    if modelo:
        filtros['modelo'] = modelo

    # Provincia y ciudad
    provincia = request.args.get('province')
    if provincia and provincia != "all":
        filtros['provincia'] = provincia

    ciudad = request.args.get('city')
    if ciudad:
        filtros['ciudad'] = ciudad

    # Kilometraje
    km_desde = request.args.get('mileage-from')
    km_hasta = request.args.get('mileage-to')
    if km_desde or km_hasta:
        filtros['kilometraje'] = {}
        if km_desde:
            filtros['kilometraje']['$gte'] = int(km_desde)
        if km_hasta:
            filtros['kilometraje']['$lte'] = int(km_hasta)

    # Año
    ano_desde = request.args.get('year-from')
    ano_hasta = request.args.get('year-to')
    if ano_desde or ano_hasta:
        filtros['ano'] = {}
        if ano_desde:
            filtros['ano']['$gte'] = int(ano_desde)
        if ano_hasta:
            filtros['ano']['$lte'] = int(ano_hasta)

    # Caballos de potencia
    cv_desde = request.args.get('horsepower-from')
    cv_hasta = request.args.get('horsepower-to')
    if cv_desde or cv_hasta:
        filtros['cv'] = {}
        if cv_desde:
            filtros['cv']['$gte'] = int(cv_desde)
        if cv_hasta:
            filtros['cv']['$lte'] = int(cv_hasta)

    # Precio
    precio_desde = request.args.get('price-from')
    precio_hasta = request.args.get('price-to')
    if precio_desde or precio_hasta:
        filtros['precio'] = {}
        if precio_desde:
            filtros['precio']['$gte'] = int(precio_desde)
        if precio_hasta:
            filtros['precio']['$lte'] = int(precio_hasta)

    # Combustible y transmisión
    combustible = request.args.get('fuel')
    if combustible:
        filtros['combustible'] = combustible

    transmision = request.args.get('transmission')
    if transmision:
        filtros['transmision'] = transmision

    # Consultar la colección con los filtros
    vehiculos = list(vehiculos_collection.find(filtros, {'_id': 0}))

    # Si no se encuentran vehículos
    if not vehiculos:
        return jsonify({'mensaje': 'No se encontraron vehículos con los filtros aplicados.', 'data': []}), 200

    mensaje = "Se han obtenido los vehículos filtrados."
    return jsonify({'mensaje': mensaje, 'data': vehiculos}), 200


# Obtener un vehículo por matrícula
@app.route('/vehiculos/<string:matricula>', methods=['GET'])
def obtener_vehiculo(matricula):
    vehiculo = vehiculos_collection.find_one({'matricula': matricula}, {'_id': 0})
    if vehiculo:
        mensaje = f"Vehículo con matrícula {matricula} encontrado."
        return jsonify({'mensaje': mensaje, 'data': vehiculo}), 200
    return jsonify({'error': 'Vehículo no encontrado'}), 404


# Agregar un vehículo
@app.route('/vehiculos', methods=['POST'])
@requiere_token
def agregar_vehiculo():
    nuevo_vehiculo = request.json

    if not nuevo_vehiculo:
        return jsonify({'error': 'Cuerpo de la solicitud vacío'}), 400

    required_fields = ['matricula', 'marca', 'modelo', 'ano', 'kilometraje',
                       'precio', 'ciudad', 'provincia', 'combustible',
                       'transmision', 'cv', 'imagenes']

    for field in required_fields:
        if field not in nuevo_vehiculo:
            return jsonify({'error': f'Falta el campo: {field}'}), 400

    try:
        ano = int(nuevo_vehiculo['ano'])
        kilometraje = int(nuevo_vehiculo['kilometraje'])
        cv = int(nuevo_vehiculo['cv'])
        precio = float(nuevo_vehiculo['precio'])

        if not (1980 <= ano <= 2024):
            return jsonify({'error': 'El año debe estar entre 1980 y 2024'}), 400

        if not (0 <= kilometraje <= 300000):
            return jsonify({'error': 'El kilometraje debe estar entre 0 y 300,000'}), 400

        if not (50 <= cv <= 500):
            return jsonify({'error': 'Los caballos deben estar entre 50 y 500'}), 400

        if not (0 <= precio <= 200000):
            return jsonify({'error': 'El precio debe estar entre 0 y 200,000'}), 400

        if nuevo_vehiculo['provincia'] == "":
            return jsonify({'error': 'La provincia no puede estar vacía'}), 400

        if nuevo_vehiculo['ciudad'] == "":
            return jsonify({'error': 'La ciudad no puede estar vacía'}), 400

        if nuevo_vehiculo['combustible'] not in ['Gasolina', 'Diésel', 'Eléctrico', 'Híbrido']:
            return jsonify({'error': 'El tipo de combustible es inválido'}), 400

        if nuevo_vehiculo['transmision'] not in ['Manual', 'Automático']:
            return jsonify({'error': 'El tipo de transmisión es inválido'}), 400

    except ValueError as e:
        return jsonify({'error': f'Error en los valores numéricos: {str(e)}'}), 400

    if vehiculos_collection.find_one({'matricula': nuevo_vehiculo['matricula']}):
        return jsonify({'error': 'Ya existe un vehículo con esta matrícula'}), 409

    try:
        vehiculos_collection.insert_one(nuevo_vehiculo)

        nuevo_vehiculo.pop('_id', None)

        mensaje = "Vehículo creado correctamente."
        return jsonify({'mensaje': mensaje, 'data': nuevo_vehiculo}), 201
    except Exception as e:
        print(f"Error al insertar el vehículo: {str(e)}")  # Log para el servidor
        return jsonify({'error': 'Error interno del servidor. Inténtalo de nuevo más tarde.'}), 500


# Actualizar un vehículo
@app.route('/vehiculos/<string:matricula>', methods=['PUT'])
@requiere_token
def actualizar_vehiculo(matricula):
    vehiculo_actualizado = request.json

    # Verificar si se está cambiando la matrícula
    if 'matricula' in vehiculo_actualizado:
        nueva_matricula = vehiculo_actualizado['matricula']
        if nueva_matricula != matricula:  # Compara la nueva matrícula con la actual
            # Verificar si ya existe un vehículo con la nueva matrícula
            if vehiculos_collection.find_one({'matricula': nueva_matricula}):
                return jsonify(
                    {'error': 'No se puede cambiar la matrícula, ya existe un vehículo con esta matrícula.'}), 409

    result = vehiculos_collection.update_one({'matricula': matricula}, {'$set': vehiculo_actualizado})

    if result.matched_count == 0:
        # No se encontró el vehículo
        return jsonify({'error': 'Vehículo no encontrado'}), 404

    if result.modified_count == 0:
        # No se realizaron cambios
        return jsonify({'error': 'No se realizaron cambios en el vehículo'}), 400

    mensaje = f"Vehículo con matrícula {matricula} actualizado exitosamente."
    return jsonify({'mensaje': mensaje, 'data': vehiculo_actualizado}), 200


# Eliminar un vehículo
@app.route('/vehiculos/<string:matricula>', methods=['DELETE'])
@requiere_token
def eliminar_vehiculo(matricula):
    result = vehiculos_collection.delete_one({'matricula': matricula})
    if result.deleted_count:
        mensaje = f"Vehículo con matrícula {matricula} eliminado exitosamente."
        return jsonify({'mensaje': mensaje}), 200
    return jsonify({'error': 'Vehículo no encontrado'}), 404


# USUARIOS

@app.route('/login', methods=['POST'])
def iniciar_sesion():
    data = request.json
    if not data or 'email' not in data or 'contrasena' not in data:
        return jsonify({'error': 'Faltan datos'}), 400

    email = data['email']
    contrasena = data['contrasena']

    # Buscar al usuario por email
    usuario = usuarios_collection.find_one({'email': email})

    if usuario:
        print(f"Usuario encontrado: {usuario}")

        # Verificar si la contraseña es correcta
        if check_password_hash(usuario['contrasena'], contrasena):
            print("Contraseña correcta")

            # Generar JWT token que expira en 48 horas
            token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=48)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            # Devolver el token y el DNI del usuario
            return jsonify({
                'mensaje': 'Inicio de sesión exitoso',
                'token': token,
                'dni': usuario['dni']
            }), 200
        else:
            print("Contraseña incorrecta")
    else:
        print("Usuario no encontrado")

    return jsonify({'error': 'El usuario o la contraseña introducida no son correctos'}), 401


# Obtener datos de contacto de un usuario por DNI
@app.route('/usuarios/<string:dni>', methods=['GET'])
def obtener_usuario(dni):
    # Devolver solo nombre, email y teléfono
    usuario = usuarios_collection.find_one({'dni': dni}, {'_id': 0, 'nombre': 1, 'email': 1, 'telefono': 1})

    if usuario:
        mensaje = f"Usuario con DNI {dni} encontrado."
        return jsonify({'mensaje': mensaje, 'data': usuario}), 200

    return jsonify({'error': 'Usuario no encontrado'}), 404


@app.route('/usuarios', methods=['POST'])
def agregar_usuario():
    nuevo_usuario = request.json

    if not nuevo_usuario:
        return jsonify({'error': 'Cuerpo de la solicitud vacío'}), 400

    if 'dni' not in nuevo_usuario:
        return jsonify({'error': 'DNI es requerido'}), 400

    # Verificar si el DNI ya existe
    if usuarios_collection.find_one({'dni': nuevo_usuario['dni']}):
        return jsonify({'error': 'Ya existe un usuario con este DNI.'}), 409

    # Verificar si la contraseña está en el cuerpo de la solicitud
    if 'contrasena' not in nuevo_usuario:
        return jsonify({'error': 'La contraseña es requerida'}), 400

    # Hashear la contraseña antes de guardarla
    nuevo_usuario['contrasena'] = generate_password_hash(nuevo_usuario['contrasena'])

    try:
        usuarios_collection.insert_one(nuevo_usuario)
        nuevo_usuario.pop('_id', None)

        mensaje = "Usuario creado correctamente."
        return jsonify({'mensaje': mensaje, 'data': nuevo_usuario}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Ver perfil del usuario autenticado
@app.route('/perfil/<string:dni>', methods=['GET'])
@requiere_token
def ver_perfil(dni):
    usuario = usuarios_collection.find_one({'dni': dni}, {'_id': 0})

    if usuario:
        mensaje = "Perfil del usuario obtenido con éxito."
        return jsonify({'mensaje': mensaje, 'data': usuario}), 200

    return jsonify({'error': 'Usuario no encontrado'}), 404


@app.route('/usuarios/<string:dni>', methods=['PUT'])
@requiere_token
def actualizar_usuario(dni):
    datos_actualizados = request.json

    # Verificar si el campo 'dni' está en los datos actualizados y si es diferente del DNI actual
    if 'dni' in datos_actualizados and datos_actualizados['dni'] != dni:
        # Comprobar si el nuevo DNI ya existe en la colección
        if usuarios_collection.find_one({'dni': datos_actualizados['dni']}):
            return jsonify({'error': 'El DNI proporcionado ya está asociado a otro usuario.'}), 409

    # Verificar si se incluye una nueva contraseña en los datos y hashearla antes de actualizarla
    if 'contrasena' in datos_actualizados:
        datos_actualizados['contrasena'] = generate_password_hash(datos_actualizados['contrasena'])

    # Realizar la actualización
    resultado = usuarios_collection.update_one({'dni': dni}, {'$set': datos_actualizados})

    if resultado.matched_count == 0:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    if resultado.modified_count == 0:
        return jsonify({'error': 'No se realizaron cambios en el usuario'}), 400

    mensaje = f"Usuario con DNI {dni} actualizado exitosamente."
    return jsonify({'mensaje': mensaje}), 200


# Eliminar un usuario por DNI
@app.route('/usuarios/<string:dni>', methods=['DELETE'])
@requiere_token
def eliminar_usuario(dni):
    resultado = usuarios_collection.delete_one({'dni': dni})
    if resultado.deleted_count > 0:
        mensaje = f"Usuario con DNI {dni} eliminado exitosamente."
        return jsonify({'mensaje': mensaje}), 200
    return jsonify({'error': 'Usuario no encontrado'}), 404


# PUBLICACIONES

# Obtener todas las publicaciones
@app.route('/publicaciones', methods=['GET'])
def obtener_publicaciones():
    publicaciones = list(publicaciones_collection.find({}))

    if not publicaciones:
        return jsonify({'mensaje': 'No se encontraron publicaciones.', 'data': []}), 404

    # Convertir _id a string en cada publicación
    for publicacion in publicaciones:
        publicacion['_id'] = str(publicacion['_id'])

    mensaje = "Se han obtenido todas las publicaciones."
    return jsonify({'mensaje': mensaje, 'data': publicaciones}), 200


# Obtener una publicación por ID
@app.route('/publicaciones/<publicacion_id>', methods=['GET'])
def obtener_publicacion(publicacion_id):
    publicacion = publicaciones_collection.find_one({'_id': ObjectId(publicacion_id)})

    if publicacion:
        # Convertir el _id a string para el JSON
        publicacion['_id'] = str(publicacion['_id'])
        return jsonify({'data': publicacion, 'mensaje': 'Publicación encontrada exitosamente.'}), 200
    else:
        return jsonify({'error': 'Publicación no encontrada.'}), 404


# Agregar una nueva publicación
@app.route('/publicaciones', methods=['POST'])
@requiere_token
def crear_publicacion():
    nueva_publicacion = request.json

    # Verificar si la matrícula del vehículo existe
    if 'matricula_vehiculo' in nueva_publicacion:
        vehiculo_existente = vehiculos_collection.find_one({'matricula': nueva_publicacion['matricula_vehiculo']})
        if not vehiculo_existente:
            return jsonify({'error': 'La matrícula del vehículo no existe.'}), 400

    # Verificar si el usuario existe
    if 'dni_usuario' in nueva_publicacion:
        usuario_existente = usuarios_collection.find_one({'dni': nueva_publicacion['dni_usuario']})
        if not usuario_existente:
            return jsonify({'error': 'El usuario no existe.'}), 400

    # Verificar si ya existe una publicación con la misma matrícula para otro usuario
    if 'matricula_vehiculo' in nueva_publicacion:
        publicacion_existente = publicaciones_collection.find_one({
            'matricula_vehiculo': nueva_publicacion['matricula_vehiculo']
        })
        if publicacion_existente:
            return jsonify({'error': 'Ya existe una publicación para el vehículo con esta matrícula.'}), 400

    # Agregar la nueva publicación sin especificar ID
    resultado = publicaciones_collection.insert_one(nueva_publicacion)
    nueva_publicacion['_id'] = str(resultado.inserted_id)

    # Mensaje de éxito
    mensaje = 'Publicación creada exitosamente.'
    return jsonify({'mensaje': mensaje, 'data': nueva_publicacion}), 201


# Actualizar una publicación
@app.route('/publicaciones/<publicacion_id>', methods=['PUT'])
@requiere_token
def actualizar_publicacion(publicacion_id):
    publicacion_actualizada = request.json

    # Verificar si la matrícula del vehículo existe, si se proporciona
    if 'matricula_vehiculo' in publicacion_actualizada:
        vehiculo_existente = vehiculos_collection.find_one({'matricula': publicacion_actualizada['matricula_vehiculo']})
        if not vehiculo_existente:
            return jsonify({'error': 'La matrícula del vehículo no existe.'}), 400

    # Verificar si el usuario existe, si se proporciona
    if 'dni_usuario' in publicacion_actualizada:
        usuario_existente = usuarios_collection.find_one({'dni': publicacion_actualizada['dni_usuario']})
        if not usuario_existente:
            return jsonify({'error': 'El usuario no existe.'}), 400

    # Verificar si ya existe otra publicación con la misma matrícula para otro usuario
    if 'matricula_vehiculo' in publicacion_actualizada:
        publicacion_existente = publicaciones_collection.find_one({
            'matricula_vehiculo': publicacion_actualizada['matricula_vehiculo'],
            '_id': {'$ne': ObjectId(publicacion_id)}  # Excluir la publicación que se está actualizando
        })
        if publicacion_existente:
            return jsonify({'error': 'Ya existe una publicación para el vehículo con esta matrícula.'}), 400

    # Actualizar la publicación
    result = publicaciones_collection.update_one({'_id': ObjectId(publicacion_id)}, {'$set': publicacion_actualizada})

    if result.matched_count == 0:
        return jsonify({'error': 'Publicación no encontrada.'}), 404

    if result.modified_count == 0:
        return jsonify({'error': 'No se realizaron cambios en la publicación.'}), 400

    mensaje = "Publicación actualizada exitosamente."
    return jsonify({'mensaje': mensaje, 'data': publicacion_actualizada}), 200


# Eliminar una publicación
@app.route('/publicaciones/<publicacion_id>', methods=['DELETE'])
@requiere_token
def eliminar_publicacion(publicacion_id):
    result = publicaciones_collection.delete_one({'_id': ObjectId(publicacion_id)})

    if result.deleted_count:
        mensaje = f"Publicación con ID {publicacion_id} eliminada exitosamente."
        return jsonify({'mensaje': mensaje}), 200
    return jsonify({'error': 'Publicación no encontrada.'}), 404


# FAVORITOS

# Obtener favoritos de un usuario por DNI
@requiere_token
@app.route('/favoritos/<string:dni_usuario>', methods=['GET'])
def obtener_favoritos_por_usuario(dni_usuario):
    favoritos = list(favoritos_collection.find({'dni_usuario': dni_usuario}, {'_id': 0}))

    if not favoritos:  # Verifica si la lista está vacía
        return jsonify({'mensaje': 'No se encontraron favoritos para este usuario.', 'data': []}), 404

    mensaje = f"Se han obtenido los favoritos del usuario {dni_usuario}."
    return jsonify({'mensaje': mensaje, 'data': favoritos}), 200


# Agregar un favorito
@app.route('/favoritos', methods=['POST'])
@requiere_token
def agregar_favorito():
    nuevo_favorito = request.json

    if not nuevo_favorito or 'dni_usuario' not in nuevo_favorito or 'matricula_vehiculo' not in nuevo_favorito:
        return jsonify({'error': 'Debe proporcionar el DNI y la matrícula.'}), 400

    # Verificar si ya existe la relación en favoritos
    favorito_existente = favoritos_collection.find_one({
        'dni_usuario': nuevo_favorito['dni_usuario'],
        'matricula_vehiculo': nuevo_favorito['matricula_vehiculo']
    })

    if favorito_existente:
        return jsonify({'error': 'El favorito ya existe.'}), 409

    try:
        # Insertar el nuevo favorito
        favoritos_collection.insert_one(nuevo_favorito)
        nuevo_favorito.pop('_id', None)  # Eliminar _id si está presente

        mensaje = "Favorito agregado correctamente."
        return jsonify({'mensaje': mensaje, 'data': nuevo_favorito}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Eliminar un favorito por DNI y matrícula
@app.route('/favoritos', methods=['DELETE'])
@requiere_token
def eliminar_favorito():
    datos_favorito = request.json

    if not datos_favorito or 'dni_usuario' not in datos_favorito or 'matricula_vehiculo' not in datos_favorito:
        return jsonify({'error': 'Debe proporcionar el DNI y la matrícula.'}), 400

    result = favoritos_collection.delete_one({
        'dni_usuario': datos_favorito['dni_usuario'],
        'matricula_vehiculo': datos_favorito['matricula_vehiculo']
    })

    if result.deleted_count:
        mensaje = "Favorito eliminado exitosamente."
        return jsonify({'mensaje': mensaje}), 200

    return jsonify({'error': 'Favorito no encontrado'}), 404


if __name__ == '__main__':
    app.run(debug=True)
