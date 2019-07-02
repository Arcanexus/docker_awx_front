#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask,jsonify,render_template, request, redirect, flash
from flask_restful import Resource, Api
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, validators, RadioField, SelectField, SelectMultipleField
from json import dumps, loads
import platform
import requests
import ldap
import os

app = Flask(__name__,template_folder='./templates/')
app.config['SECRET_KEY'] = 'apple pie, because why not.'
api = Api(app)
if "BOUCHON" in os.environ:
  bouchon = os.environ['BOUCHON']
else:
  bouchon = "False"

if "AWX_URL" in os.environ:
  awx_url = os.environ['AWX_URL']
else:
  awx_url = 'http://127.0.0.1:5002' # default bouchon

if "AWX_TOKEN" in os.environ:
  awx_token = os.environ['AWX_TOKEN']
else:
  awx_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # local awx admin test token

class MyForm(FlaskForm):
   name = StringField('Nom', validators=[validators.DataRequired()])
   age = IntegerField('Âge', [validators.DataRequired(), validators.Length(min=1, max=3)])
   remember_me = BooleanField('Se souvenir de moi')
   submit = SubmitField('Valider')

class CreateVMForm(FlaskForm):
  target_env = SelectField('Target Environment', choices=[('Development', 'Development'), ('Homologation', 'Homologation'), ('Production', 'Production')], default='Development', validators=[validators.DataRequired()])
  target_site = SelectField('Target Site', choices=[('PN1','PN1'), ('PN2','PN2'), ('SD1','SD1')], default='PN1', validators=[validators.DataRequired()])
  app_trigram = StringField('App Trigram', validators=[validators.DataRequired(), validators.Length(min=3, max=3, message="App Trigram must contain 3 characters")])
  vm_owner_domain = SelectField('Owner', choices=[('D12','D12'), ('GSY','GSY')], default='D12', validators=[validators.DataRequired()])
  vm_owner_gaia = StringField('Gaia', validators=[validators.DataRequired(), validators.Regexp('^[a-zA-Z]{2}\d{4}(-(a|o)|)$', message="Username format : XX1234(-a|-o)")])
  vm_os = SelectField('Operating System', choices=[('Windows2016', 'Windows 2016')], default='Windows2016', validators=[validators.DataRequired()])
  vm_cpu_count = SelectField('CPU Count', choices=[('1','1'), ('2','2'), ('3','3') , ('4', '4')], default='2', validators=[validators.DataRequired()])
  vm_ram_size = SelectField('RAM', choices=[('1024','1024'), ('2048','2048'), ('3072','3072'), ('4096','4096'), ('8192','8192')], default='4096', validators=[validators.DataRequired()])
  vm_disk_size = IntegerField('System Disk Size', default='50', validators=[validators.DataRequired(), validators.Regexp('^\d+$', message="Invalid format")])
  vm_name = StringField('VM Name', validators=[validators.Length(min=0, max=15, message="VM name has 15 characters max.")])
  vm_count = IntegerField('Count', default=1, validators=[validators.DataRequired(), validators.Regexp('^\d+$', message="Invalid format")])
  create_button = SubmitField('Create')

class ResetForm(FlaskForm):
   resetdb = SubmitField(label='ResetDB')

@app.route('/', methods=['POST','GET'])
def home():
  mots = ["Bonjour", "à", "toi,", "anonyme citoyen."]
  form = MyForm()
  resetform = ResetForm()
  createvmform = CreateVMForm()
  

  if resetform.resetdb.data:
    session = requests.Session()
    session.trust_env = False
    response4 = session.get(awx_url + '/reset', allow_redirects=True)
    print(response4.text)
    return redirect('/')

  if createvmform.create_button.data:
    headers = {}
    headers['Authorization'] = "Bearer " + awx_token
    headers['Content-Type'] = "application/json"
    headers['Accept'] = "application/json"

    extra_vars = {}
    payload = {}
    extra_vars['target_env'] = createvmform.target_env.data
    extra_vars['site'] = createvmform.target_site.data
    extra_vars['application_trigram'] = createvmform.app_trigram.data
    extra_vars['owner'] = createvmform.vm_owner_domain.data + '\\' + createvmform.vm_owner_gaia.data
    extra_vars['operating_system'] = createvmform.vm_os.data
    extra_vars['cpu_count'] = str(createvmform.vm_cpu_count.data)
    extra_vars['ram_size'] = str(createvmform.vm_ram_size.data)
    extra_vars['disk_size'] = str(createvmform.vm_disk_size.data)
    extra_vars['vmname'] = createvmform.vm_name.data
    payload['extra_vars'] = extra_vars

    # Bouchon
    session = requests.Session()
    session.trust_env = False
    
    list_wf_templates = session.get(awx_url + '/api/v2/workflow_job_templates/', headers=headers)
    res_json=loads(list_wf_templates.content)
    output_dict = [x for x in res_json['results'] if x['name'] == 'Create Windows VM On Premise']
    create_vm_workflow_id = output_dict[0]['id']
    print('Id du workflow : ' + str(create_vm_workflow_id))
    
    response3 = session.post(awx_url + '/api/v2/workflow_job_templates/' + str(create_vm_workflow_id) + '/launch/', data=dumps(payload), headers=headers, allow_redirects=True)
    print(response3.text)
    if bouchon == 'True':
      response4 = session.get(awx_url, allow_redirects=True)
      parsed = loads(response4.text)    
      flash('{}'.format(dumps(parsed, indent=4, sort_keys=True)))

    return redirect('/')
    
  else:
    return render_template('index.html', titre="Bienvenue !", mots=mots, form=createvmform, resetform=resetform, bouchon=bouchon)

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
