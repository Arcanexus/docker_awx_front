# app.py - a minimal flask api using flask_restful
from flask import Flask,jsonify
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

@app.route('/')
def index():
   return "Ceci est la page d'accueil."
   
@app.route('/hello/<phrase>')
def hello(phrase):
   return phrase

@app.route('/json')
def index_json():
   return jsonify({'hello': 'world'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
