from flask import Flask, request, jsonify, Response
from flask_pymongo import PyMongo
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from bson import json_util
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI_ENV = os.getenv('MONGO_URI_ENV') 

app = Flask(__name__)
CORS(app)

app.config['MONGO_URI'] = str(MONGO_URI_ENV)
mongo = PyMongo(app)

@app.route('/', methods=['GET'])
def index():
    return {
        'message': 'API de inventario de servicios',
        'routes': [
            {'route':'/servicios', 'method': 'GET', 'result': 'Get all services'},
            {'route':'/servicio/<codigo>', 'method': 'GET', 'result': 'Get a service from codigo'},
            {'route':'/servicio/<codigo>', 'method': 'DELETE', 'result': 'Delete a service from codigo'},
            {'route':'/servicio/<codigo>', 'method': 'PUT', 'result': 'Update a service from codigo'},
            {'route':'/servicio/<codigo>', 'method': 'POST', 'result': 'Add a service from the body via a json', 
             'format_body':{
            'codigo': 'String codigo',
            'aplicacion': 'String aplicación, sólo tres tipos --> Manos, Pies or Pestañas',
            'servicio': 'String servicio, detalla el servicio que se ofrece para esa aplicación',
            'precio': 'String precio',}},
            ],
    }

# routes CRUD for servicios
@app.route('/servicios', methods=['GET'])
def get_servicios():
    result = mongo.db.servicios.find()
    response = json_util.dumps(result)
    response_json = Response(response, mimetype='application/json').json    
    response_message = jsonify({ 
            'message': 'Listing all services successfully', 
            'services': response_json,
    })
    response_message.status_code = 200
    return response_message

@app.route('/servicio/<codigo>', methods=['GET'])
def get_service(codigo):
    result = mongo.db.servicios.find_one({'codigo': codigo})
    if result is not None:
        response = json_util.dumps(result)
        response_json = Response(response, mimetype='application/json').json
        response_ok =  jsonify({
            'message': 'Service found successfully', 
            '_id': response_json['_id'],
            'codigo':response_json['codigo'],
            'aplicacion':response_json['aplicacion'],
            'servicio':response_json['servicio'],
            'precio':response_json['precio'],
        })
        response_ok.status_code = 200
        return response_ok
    else:
        return not_found()

@app.route('/servicio/<codigo>', methods=['DELETE'])
def service_delete(codigo):
    result = mongo.db.servicios.delete_one({'codigo': codigo})
    if result.deleted_count == 1:
        return {
            'message': 'Service was deleted successfully',
            'codigo': codigo,
        }
    else:
        return not_found()

@app.route('/servicio/<codigo>', methods=['PUT'])
def update_servicios(codigo):
    aplicacion, servicio, precio = request.json.values()
    if aplicacion and servicio and precio:
        
        result = mongo.db.servicios.find_one_and_update({'codigo': codigo}, {'$set':{
            'aplicacion': aplicacion,'servicio': servicio,'precio': precio,
            }})
        if result is not None:
            response = json_util.dumps(result)
            response_json = Response(response, mimetype='application/json').json
            response_message = {
            'message': 'service updated successfully',
            '_id': response_json['_id'],
            'codigo': response_json['codigo'],
            'service_new': {
                'aplicacion': aplicacion,
                'servicio': servicio,
                'precio': precio,},
            'service_old':{
                'aplicacion':response_json['aplicacion'] ,
                'servicio': response_json['servicio'] ,
                'precio': response_json['precio'],
                }
            }
            return  response_message
        else:
            return not_found()


@app.route('/servicio', methods=['POST'])
def create_service():
    codigo, aplicacion, servicio, precio = request.json.values()
    # Consulto si ya existe un servicio con ese codigo
    result_get = get_service(codigo)
    if result_get.status_code != 404:
        error = error_create('This service '+codigo+' already exists')
        error_response = error.json
        return  error_response
        
    # Si el servicio con ese codigo no existe se crea el servicio
    if codigo and aplicacion and servicio and precio:
        result = mongo.db.servicios.insert_one(
            {'codigo': codigo, 'aplicacion': aplicacion, 'servicio': servicio, 'precio': precio,}
        )
        return{
            'message': 'Created services successfully',
            '_id': str(result.inserted_id),
            'codigo': codigo,
            'aplicacion': aplicacion,
            'servicio': servicio,
            'precio': precio,
            }
    else:
        return error_create('Invalid Data')


# routes for cart

# routes for users
# terminar de crear la validación por usuario, también debo agregar en el front
@app.route('/users', methods=['GET'])
def get_users():
    result = mongo.db.users.find()
    response = json_util.dumps(result)
    response_json = Response(response, mimetype='application/json').json
    response_message = {
        'message': 'Listing all users successfully',
        'users': response_json,
    }
    return response_message

@app.route('/users', methods=['POST'])
def create_user():
    username ,email, password = request.json.values()
    
    if username and email and password:
        hashed_password = generate_password_hash(password)
        result = mongo.db.users.insert_one(
            {'username': username, 'email': email, 'password': hashed_password}
        )
        return{
            'message': 'Created user',
            '_id': str(result.inserted_id),
            'username': username,
            'email': email,
            'password': hashed_password,
            }
    else:
        return error_create('Invalid Data')

# cuando ocurre un error va a ser manejado con estas funciones
@app.errorhandler(404)
def not_found(error=404):
    response = jsonify({
        'message': 'Resource not found ' + request.url  + ' ' + str(error),
        'status': 404,
    })
    response.status_code = 404 
    return response

@app.errorhandler(400)
def error_create(message, error=400):
    response =  jsonify({
        'message': 'Error creating resource in ' + request.url + '  ' + str(message)  + ' ' + str(error),
        'status': 400,
    })
    response.status_code = 400
    return response

@app.errorhandler(500)
def error_create(error=500):
    response =  jsonify({
        'message': 'Internal server error ' + request.url + ' ' + str(error),
        'status': 500,
    })
    response.status_code = error
    return response

if __name__ == '__main__':
     app.run(debug=True)