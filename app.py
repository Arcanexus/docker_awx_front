# app.py - a minimal flask api using flask_restful
from flask import Flask,jsonify
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

@app.route('/')
def home():
   mots = ["bonjour", "à", "toi,", "anonyme citoyen."]
   return render_template('index.html', titre="Bienvenue !", mots=mots)

@app.route('/hello/<phrase>')
def hello(phrase):
   return phrase

@app.route('/json')
def index_json():
   return jsonify({'hello': 'world'})

@app.errorhandler(404)
def ma_page_404(error):
    return "Hahaha 404, N00b !", 404

   
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
