# app.py - a minimal flask api using flask_restful
from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

@app.route('/')
def index():
   return "Ceci est la page d'accueil."
   
@app.route('/hello/<phrase>')
def hello(phrase):
   return phrase

class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

@app.route('/json')
api.add_resource(HelloWorld, '/json')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
