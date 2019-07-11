#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask,jsonify,render_template, request, redirect, flash, Blueprint
from flask_restplus import Resource, Api, Namespace, fields
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, validators, RadioField, SelectField, SelectMultipleField
from json import dumps, loads
import platform
import requests
# import ldap
import os, sys
from api import azure, onpremise, common

app = Flask(__name__,template_folder='./templates/')
app.config['SECRET_KEY'] = 'apple pie, because why not.'
blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(blueprint, version='1.0', title='GIAC API', description='GIAC automation RESTfull API')
ns_onpremise = api.namespace('onpremise', description='Operation for VM on VMWare')
ns_azure = api.namespace('azure', description='Operation for VM on Azure')
app.register_blueprint(blueprint)

if "BOUCHON" in os.environ:
  bouchon = os.environ['BOUCHON']
else:
  bouchon = "False"

if "AWX_URL" in os.environ:
  awx_url = os.environ['AWX_URL']
else:
  #awx_url = 'http://127.0.0.1:5002' # default bouchon
  awx_url = 'http://10.20.102.6'
if "AWX_TOKEN" in os.environ:
  awx_token = os.environ['AWX_TOKEN']
else:
  #awx_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # local awx admin test token
  awx_token = 'IH8zKI3k46jCoLuy36ccOVzpht7XFG' # local awx admin test token

# check AWX connection
check_res = common.checkAWXconnection(awx_url=awx_url, awx_token=awx_token)
if check_res != 200:
  sys.exit("Impossible to connect to AWX [" + awx_url + "]")
else:
  print("Connected to AWX [" + awx_url + "]")

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

class DeleteVMForm(FlaskForm):
  vm_name = StringField('VM Name', validators=[validators.Length(min=0, max=15, message="VM name has 15 characters max.")])
  target_env = SelectField('Target Environment', choices=[('Development', 'Development'), ('Homologation', 'Homologation'), ('Production', 'Production')], default='Development', validators=[validators.DataRequired()])
  delete_button = SubmitField('Delete')

class GetInfosForm(FlaskForm):
  wf_id = IntegerField('Id', validators=[validators.DataRequired()])
  getinfos_button = SubmitField('Get Infos')

class ResetForm(FlaskForm):
  resetdb = SubmitField(label='ResetDB')

@app.route('/', methods=['POST','GET'])
def home():
  mots = ["Bonjour", "à", "toi,", "anonyme citoyen."]
  form = MyForm()
  resetform = ResetForm()
  createvmform = CreateVMForm()
  deletevmform = DeleteVMForm()
  getinfosform = GetInfosForm()
  
  if resetform.resetdb.data:
    session = requests.Session()
    session.trust_env = False
    response4 = session.get(awx_url + '/reset', allow_redirects=True, verify=False)
    print(response4.text)
    return redirect('/')

  if createvmform.create_button.data:
    
    extra_vars = {}
    payload = {}
    extra_vars['target_env'] = createvmform.target_env.data
    extra_vars['site'] = createvmform.target_site.data
    extra_vars['application_trigram'] = createvmform.app_trigram.data
    extra_vars['owner'] = createvmform.vm_owner_gaia.data
    extra_vars['operating_system'] = createvmform.vm_os.data
    extra_vars['cpu_count'] = int(createvmform.vm_cpu_count.data)
    extra_vars['ram_size'] = int(createvmform.vm_ram_size.data)
    extra_vars['disk_size'] = str(createvmform.vm_disk_size.data)
    extra_vars['vmname'] = createvmform.vm_name.data
    payload['extra_vars'] = extra_vars

    # Bouchon
    result = onpremise.createVMOnPremise(awx_url=awx_url, awx_token=awx_token, payload=payload)
    
    if bouchon == 'True':
      session = requests.Session()
      session.trust_env = False
      bouchonContent = session.get(awx_url, allow_redirects=True, verify=False)
      parsed = loads(bouchonContent.text)    
      flash('{}'.format(dumps(parsed, indent=4, sort_keys=True)))
    else:
      flash('{}'.format(dumps(result, indent=4, sort_keys=True)))

    return redirect('/#flash')
  
  elif deletevmform.delete_button.data:
    
    extra_vars = {}
    payload = {}
    extra_vars['target_env'] = createvmform.target_env.data
    extra_vars['vm_name'] = createvmform.vm_name.data
    payload['extra_vars'] = extra_vars

    result = onpremise.deleteVMOnPremise(awx_url=awx_url, awx_token=awx_token, payload=payload)
    flash('{}'.format(dumps(result, indent=4, sort_keys=True)))
    return redirect('/#flash')

  elif getinfosform.getinfos_button.data:
    result = onpremise.getVMOnPremiseInfos(awx_url=awx_url, awx_token=awx_token, wf_id=getinfosform.wf_id.data)
    flash('{}'.format(dumps(result, indent=4, sort_keys=True)))
    return redirect('/#flash')

  else:
    return render_template('index.html', 
      titre="GIAC Portal",
      mots=mots,
      form=createvmform,
      resetform=resetform,
      deletevmform=deletevmform,
      getinfosform=getinfosform,
      bouchon=bouchon)

create_onprem_model = ns_onpremise.model('Create a VM On Premise', {
  'vmname': fields.String(description='The name of the VM'),
  'target_env': fields.String(required=True, description='The target environment'),
  'site': fields.String(required=True, description='The target site'),
  'application_trigram': fields.String(required=True, description='The target environment'),
  'owner': fields.String(required=True, description='The VM owner Gaia'),
  'operating_system': fields.String(required=True, description='The VM OS'),
  'cpu_count': fields.Integer(required=True, description='The number of CPU of the VM'),
  'ram_size': fields.Integer(required=True, description='The RAM size of the VM'),
  'disk_size': fields.String(required=True, description='The VM disk size')
})

delete_onprem_model = ns_onpremise.model('Delete a VM On Premise', {
  'vm_name': fields.String(description='The name of the VM'),
  'target_env': fields.String(required=True, description='The target environment')
})

get_onprem_model = ns_onpremise.model('Get VM On Premise infos', {
  'wf_id': fields.Integer(description='The AWX Job Id')
})

@ns_onpremise.route('/<int:id>')
#@ns_onpremise.doc(params={'awx_url': 'AWX base URL', 'awx_token': 'AWX access token', 'payload': 'JSON payload'})
@ns_onpremise.doc(params={'id': 'AWX Job Id'})
class GetOnPremise(Resource):            #  Create a RESTful resource
  # @ns_onpremise.expect(get_onprem_model)
  def get(self, id):
    """
    Get infos from on premise VM workflow
    """
    return onpremise.getVMOnPremiseInfos(awx_url=awx_url, awx_token=awx_token, wf_id=id)

@ns_onpremise.route('/')
class PostOnPremise(Resource):            #  Create a RESTful resource
  @ns_onpremise.expect(create_onprem_model)
  def post(self):                     #  Create POST endpoint
    """
    Create a VM on premise on VMWare
    """

    extra_vars = {}
    payload = {}
    extra_vars['target_env'] = api.payload['target_env']
    extra_vars['site'] = api.payload['site']
    extra_vars['application_trigram'] = api.payload['application_trigram']
    extra_vars['owner'] = api.payload['owner']
    extra_vars['operating_system'] = api.payload['operating_system']
    extra_vars['cpu_count'] = int(api.payload['cpu_count'])
    extra_vars['ram_size'] = int(api.payload['ram_size'])
    extra_vars['disk_size'] = str(api.payload['disk_size'])
    extra_vars['vmname'] = api.payload['vmname']
    payload['extra_vars'] = extra_vars

    return onpremise.createVMOnPremise(awx_url=awx_url, awx_token=awx_token, payload=payload)
  
  @ns_onpremise.expect(delete_onprem_model)
  def delete(self):
    """
    Delete a VM on premise on VMWare
    """
    extra_vars = {}
    payload = {}
    extra_vars['target_env'] = api.payload['target_env']
    extra_vars['vm_name'] = api.payload['vm_name']
    payload['extra_vars'] = extra_vars

    return onpremise.deleteVMOnPremise(awx_url=awx_url, awx_token=awx_token, payload=payload)

@ns_azure.route('/')
class Azure(Resource):            #  Create a RESTful resource
  def post(self):                     #  Create GET endpoint
    """
    Create a VM in Azure cloud
    """
    return azure.createAzureVM(vmname='test', vmsize='big')

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
  app.run(debug=True, host='0.0.0.0', port='5003')
