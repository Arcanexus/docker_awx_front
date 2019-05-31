# -*- coding:utf-8 -*-

from flask import Flask,jsonify,render_template
from flask_restful import Resource, Api
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

app = Flask(__name__,template_folder='./templates/')
app.config['SECRET_KEY'] = 'apple pie'
api = Api(app)

class MyForm(FlaskForm):
   name = StringField('name', validators=[DataRequired()])
   age = IntegerField('age', validators=[DataRequired()])
   remember_me = BooleanField('Remember Me')
   submit = SubmitField('Sign In')

@app.route('/', methods=['POST','GET'])
def home():
  mots = ["bonjour", "à", "toi,", "anonyme citoyen."]
  form = MyForm()

  if form.validate_on_submit():
    flash('Login requested for user {}, remember_me={}'.format(
      form.name.data, form.remember_me.data))
    return redirect('/hello/' + forn.name.data + ', you have ' + form.age.data + ' years old.')
  return render_template('index.html', titre="Bienvenue !", mots=mots, form=form)

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
  app.run(debug=True, host='0.0.0.0', port='5000')
