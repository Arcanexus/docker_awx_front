# -*- coding:utf-8 -*-

from flask import Flask,jsonify,render_template
from flask_restful import Resource, Api
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

class MyForm(FlaskForm):
   name = StringField('name', validators=[DataRequired()])
   age = IntegerField('age', validators=[DataRequired()])

app = Flask(__name__)
api = Api(app)

@app.route('/')
def home():
   mots = ["bonjour", "à", "toi,", "anonyme citoyen."]
   return render_template('./index.html', titre="Bienvenue !", mots=mots)

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
