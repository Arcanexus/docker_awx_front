# -*- coding:utf-8 -*-

from flask import Flask,jsonify,render_template, request, redirect, flash
from flask_restful import Resource, Api
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, validators
from json import dumps
import platform
import requests

app = Flask(__name__,template_folder='./templates/')
app.config['SECRET_KEY'] = 'apple pie'
api = Api(app)
url = 'http://127.0.0.1:5002/'

class MyForm(FlaskForm):
   name = StringField('Nom', validators=[validators.DataRequired()])
   age = IntegerField('Âge', [validators.DataRequired(), validators.Length(min=1, max=3)])
   remember_me = BooleanField('Se souvenir de moi')
   submit = SubmitField('Valider')

@app.route('/', methods=['POST','GET'])
def home():
  mots = ["Bonjour", "à", "toi,", "anonyme citoyen."]
  form = MyForm()

  if form.submit.data:
    flash('Bienvenue {}, âgé de {}. {forget}'.format(form.name.data, form.age.data, forget="Nous ne toublieront pas." if form.remember_me.data else ""))
    body = {}
    body['name'] = form.name.data
    body['age'] = form.age.data
    if form.remember_me.data:
      body['remember_me'] = "Nous ne toublieront pas."
    else:
      body['remember_me'] = ""
    
    response1 = requests.post(url, data=dumps(body), allow_redirects=True)
    response2 = requests.get(url, allow_redirects=True)
    
    return redirect('/')
    # return redirect('/hello/' + form.name.data + ', you have ' + str(form.age.data) + ' years old.')
  else:
    return render_template('index.html', titre="Bienvenue !", mots=mots, form=form)

@app.route('/hello/<phrase>')
def hello(phrase):
   return phrase

@app.route('/json')
def index_json():
   return jsonify({'hello': 'world'})

@app.route('/version')
def index_version():
   return platform.python_version()

@app.errorhandler(404)
def ma_page_404(error):
    return render_template('404.html', titre="Hahaha 404, N00b !"), 404

   
if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port='5001')
