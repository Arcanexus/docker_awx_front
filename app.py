#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask,render_template, request, redirect, flash, Blueprint, Response
from flask_restplus import Resource, Api, Namespace, fields
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, validators, RadioField, SelectField, SelectMultipleField
from json import dumps, loads
import platform
import requests
# import ldap
import logging
import os, sys, re
from awx_api import common, config

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console and file handlers and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fh = logging.FileHandler('awx_portal.log')
fh.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)

logger.info('================================================================================')
logger.info('=                               AWX PORTAL                                     =')
logger.info('================================================================================')

missing_config = True
conf = config.readConfig()
if conf != 1:
  awx_token = conf['awx_token']
  missing_config = False
else: # ONLY FOR LOCAL TESTING PURPOSE
    # awx_token = 'rDxTKN2vgQYMNvHjatvEFQdcxp8DHT' # local awx admin test token
    awx_token=''

if "AWX_URL" in os.environ:
  awx_url = os.environ['AWX_URL']
else:
  awx_url = 'http://10.20.102.6'
matching = re.match('^http(s|)://giacportal(|-)((|dev|hom)(|[0-9]))\.gem\.myengie\.com(|/)$',awx_url)
if matching:
  if matching.group(3) == '':
    env = 'PROD'
  else:
    env = matching.group(3)
else:
  env = 'LOCAL'

app = Flask(__name__,template_folder='./templates/')
app.config['SECRET_KEY'] = 'apple pie, because why not.'
blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
check_con = common.checkAWXconnection(awx_url=awx_url)
api = Api(blueprint,
  version='1.0', 
  title='GIAC API for ' + env.upper(), 
  description='[ <a href="/">HOME</a> ] [ Connected to AWX : <a href="'+awx_url+'">' + env.upper() + '</a> ]')

ns_onpremise = api.namespace('onpremise', description='Operation for VM on VMWare')
ns_azure = api.namespace('azure', description='Operation for VM on Azure')
ns_infos = api.namespace('infos', description="Jobs or Workflows informations")
app.register_blueprint(blueprint)

# check AWX connection
check_res = common.checkAWXconnection(awx_url=awx_url)
if check_res != 200:
  logger.error('Impossible to connect to AWX [' + awx_url + ']')
  missing_config = True
else:
  logger.info("Connected to " + env.upper() + "AWX [" + awx_url + "]")
  missing_config = False
logger.info("AWX Portal successfully started.")

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
  create_button = SubmitField('Create On Premise VM')

class CreateAzureVMForm(FlaskForm):
  vm_owner_gaia = StringField('Gaia', validators=[validators.DataRequired(), validators.Regexp('^[a-zA-Z]{2}\d{4}(-(a|o)|)$', message="Username format : XX1234(-a|-o)")])
  vm_os = SelectField('Operating System', choices=[('Windows2016', 'Windows 2016')], default='Windows2016', validators=[validators.DataRequired()])
  vm_name = StringField('VM Name', validators=[validators.Length(min=0, max=15, message="VM name has 15 characters max.")])
  vm_resourcegroup = StringField('Resource group', validators=[validators.DataRequired()])
  vm_image = StringField('Source image name', validators=[validators.DataRequired()])
  vm_size = SelectField('VM Size',choices=[('Standard_A2_v2', 'Standard_A2_v2'),  ('Standard_A8_v2', 'Standard_A8_v2'),  ('Standard_A8m_v2', 'Standard_A8m_v2'),  ('Standard_B8ms', 'Standard_B8ms'),  ('Standard_D2_v3', 'Standard_D2_v3'),  ('Standard_D4_v3', 'Standard_D4_v3'),  ('Standard_DS12_v2', 'Standard_DS12_v2'),  ('Standard_DS4_v2', 'Standard_DS4_v2'),  ('Standard_DS5_v2', 'Standard_DS5_v2'),  ('Standard_E16s_v3', 'Standard_E16s_v3'),  ('Standard_E64is_v3', 'Standard_E64is_v3'),  ('Standard_F16s_v2', 'Standard_F16s_v2'),  ('Standard_F8s', 'Standard_F8s'),  ('Standard_B2ms', 'Standard_B2ms'),  ('Standard_B1ms', 'Standard_B1ms'),  ('Standard_B2s', 'Standard_B2s'),  ('Standard_DS13_v2', 'Standard_DS13_v2'),  ('Standard_DS14_v2', 'Standard_DS14_v2'),  ('Standard_D3_v2', 'Standard_D3_v2'),  ('Standard_DS1_v2', 'Standard_DS1_v2'),  ('Standard_DS2_v2', 'Standard_DS2_v2')], validators=[validators.DataRequired()])
  vm_dc = SelectField('DC', choices=[('CTO', 'CTO'), ('Meteor', 'Meteor'), ('Gemstone', 'Gemstone'), ('Power', 'Power'), ('Bulk', 'Bulk'), ('Gas', 'Gas'), ('Transversal', 'Transversal'), ('GSSNGE', 'GSSNGE'), ('Infra', 'Infra')], validators=[validators.DataRequired()])
  createaz_button = SubmitField('Create Azure VM')

class DeleteVMForm(FlaskForm):
  vm_name = StringField('VM Name', validators=[validators.Length(min=0, max=15, message="VM name has 15 characters max.")])
  target_env = SelectField('Target Environment', choices=[('Development', 'Development'), ('Homologation', 'Homologation'), ('Production', 'Production')], default='Development', validators=[validators.DataRequired()])
  delete_button = SubmitField('Delete On Premise VM')

class DeleteAzureVMForm(FlaskForm):
  vmname = StringField('VM Name', validators=[validators.Length(min=0, max=15, message="VM name has 15 characters max.")])
  resource_group = StringField('Resource group', validators=[validators.DataRequired()])
  deleteaz_button = SubmitField('Delete Azure VM')

class GetInfosForm(FlaskForm):
  item_id = IntegerField('Id', validators=[validators.DataRequired()])
  getinfos_button = SubmitField('Get Infos')



@app.route('/', methods=['POST','GET'])
def home():
  mots = ["Bonjour", "à", "toi,", "anonyme citoyen."]
  createvmform = CreateVMForm()
  createazvmform = CreateAzureVMForm()
  deletevmform = DeleteVMForm()
  deleteazvmform = DeleteAzureVMForm()
  getinfosform = GetInfosForm()
  
  missing_config = True
  conf = config.readConfig()
  if conf != 1:
    missing_config = False

  if createvmform.create_button.data:
    if missing_config:
      logger.error('Missing configuration : awx_token')
      return 'Internal Error : Missing configuration : awx_token'
    
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Impossible to connect to AWX [' + awx_url + ']'
    
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

    logger.info('Creating a VM on Premise with the following parameters : ' + dumps(payload['extra_vars']))
    result = common.launchAWXItem(awx_url=awx_url, awx_token=conf['awx_token'], item_type='workflow_job_templates', item_name='Create Windows VM On Premise', payload=payload)
    # flash('{}'.format(dumps(result, indent=4, sort_keys=True)))
    # return redirect('/#flash')
    return redirect('/api/v1/infos/' + str(result['id']))
  
  elif deletevmform.delete_button.data:
    if missing_config:
      logger.error('Missing configuration : awx_token')
      return 'Internal Error : Missing configuration : awx_token'
    
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Impossible to connect to AWX [' + awx_url + ']'
    
    extra_vars = {}
    payload = {}
    extra_vars['target_env'] = deletevmform.target_env.data
    extra_vars['vm_name'] = deletevmform.vm_name.data
    payload['extra_vars'] = extra_vars

    logger.info('Deleting a VM on Premise with the following parameters : ' + dumps(payload['extra_vars']))
    result = common.launchAWXItem(awx_url=awx_url, awx_token=conf['awx_token'], item_type='workflow_job_templates', item_name='Delete Windows VM On Premise', payload=payload)
    # flash('{}'.format(dumps(result, indent=4, sort_keys=True)))
    # return redirect('/#flash')
    return redirect('/api/v1/infos/' + str(result['id']))

  elif createazvmform.createaz_button.data:
    if missing_config:
      logger.error('Missing configuration : awx_token')
      return 'Internal Error : Missing configuration : awx_token'
    
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Impossible to connect to AWX [' + awx_url + ']'
    
    extra_vars = {}
    payload = {}
    extra_vars['resource_group'] = createazvmform.vm_resourcegroup.data
    extra_vars['image'] = createazvmform.vm_image.data
    extra_vars['size'] = createazvmform.vm_size.data
    extra_vars['owner'] = createazvmform.vm_owner_gaia.data
    extra_vars['operating_system'] = createazvmform.vm_os.data
    extra_vars['target_dc'] = createazvmform.vm_dc.data
    extra_vars['vmname'] = createazvmform.vm_name.data
    payload['extra_vars'] = extra_vars

    logger.info('Creating an Azure VM with the following parameters : ' + dumps(payload['extra_vars']))
    result = common.launchAWXItem(awx_url=awx_url, awx_token=conf['awx_token'], item_type='workflow_job_templates', item_name='Create Windows VM On Azure', payload=payload)
    # flash('{}'.format(dumps(result, indent=4, sort_keys=True)))
    # return redirect('/#flash')
    return redirect('/api/v1/infos/' + str(result['id']))

  elif deleteazvmform.deleteaz_button.data:
    if missing_config:
      logger.error('Missing configuration : awx_token')
      return 'Internal Error : Missing configuration : awx_token'
    
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Impossible to connect to AWX [' + awx_url + ']'
    
    extra_vars = {}
    payload = {}
    extra_vars['resource_group'] = deleteazvmform.resource_group.data
    extra_vars['vmname'] = deleteazvmform.vmname.data
    payload['extra_vars'] = extra_vars

    logger.info('Deleting an Azure VM with the following parameters : ' + dumps(payload['extra_vars']))
    result = common.launchAWXItem(awx_url=awx_url, awx_token=conf['awx_token'], item_type='job_templates', item_name='Remove azure VM', payload=payload)
    # flash('{}'.format(dumps(result, indent=4, sort_keys=True)))
    # return redirect('/#flash')
    return redirect('/api/v1/infos/' + str(result['id']))

  elif getinfosform.getinfos_button.data:
    if missing_config:
      logger.error('Missing configuration : awx_token')
      return 'Internal Error : Missing configuration : awx_token'
    
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Impossible to connect to AWX [' + awx_url + ']'
    
    logger.info('Getting information for the following AWX workflow : ' + str(getinfosform.item_id.data))
    result = common.getAWXInfos(awx_url=awx_url, awx_token=conf['awx_token'], item_id=getinfosform.item_id.data)
    flash('{}'.format(dumps(result, indent=4, sort_keys=True)))
    return redirect('/api/v1/infos/' + str(getinfosform.item_id.data))

  else:
    if missing_config:
      logger.error('Missing configuration : awx_token')
      flash('ERROR : Missing configuration : awx_token')
      return redirect('/config')
    else:
      check_con = common.checkAWXconnection(awx_url=awx_url)
      if check_con != 200:
        logger.error('Impossible to connect to AWX [' + awx_url + ']')
        missing_config = True
        connection_ok = False
      else:
        connection_ok = True

      return render_template('index.html', 
        titre=env.upper() + " GIAC Portal",
        connection_ok=connection_ok,
        mots=mots,
        form=createvmform,
        createazvmform=createazvmform,
        deletevmform=deletevmform,
        deleteazvmform=deleteazvmform,
        getinfosform=getinfosform)

@app.route('/config', methods=['POST','GET'])
def config_awx():
  class ConfigForm(FlaskForm):
    config_token = config.readConfig()
    if config_token != 1:
      # TODO : secure access
      # awx_token = StringField('AWX Token', validators=[validators.DataRequired()], default=config_token['awx_token'])
      awx_token = StringField('AWX Token', validators=[validators.DataRequired()])
    else:
      awx_token = StringField('AWX Token', validators=[validators.DataRequired()])
    save_button = SubmitField(label='Save')
  
  configform = ConfigForm()
  if configform.save_button.data:
    config.writeConfig(awx_token=configform.awx_token.data)
    awx_token = config.readConfig()['awx_token']
    return redirect('/')
  else:
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      logger.error('Impossible to connect to AWX [' + awx_url + ']')
      missing_config = True
      connection_ok = False
    else:
      connection_ok = True
    return render_template('config.html', form=configform, connection_ok=connection_ok, awx_url=awx_url)

create_onprem_model = ns_onpremise.model('Create a VM On Premise', {
  'vmname': fields.String(description='The name of the VM'),
  'target_env': fields.String(required=True, description='The target environment', enum=['Development', 'Homologation', 'Production']),
  'site': fields.String(required=True, description='The target site', enum=['PN1', 'PN2', 'SD1']),
  'application_trigram': fields.String(required=True, description='The target environment', min_length=3, max_length=3),
  'owner': fields.String(required=True, description='The VM owner Gaia', pattern='^[a-zA-Z]{2}\d{4}(-(a|o)|)$'),
  'operating_system': fields.String(required=True, description='The VM Operatig System', example='Windows2016', enum=['Windows2016']),
  'cpu_count': fields.Integer(required=True, description='The number of CPU of the VM', min=1, max=8),
  'ram_size': fields.Integer(required=True, description='The RAM size of the VM', min=1024, max=32768),
  'disk_size': fields.String(required=True, description='The VM disk size')
})

create_azurevm_model = ns_azure.model('Create an azure VM from an image', {
  'vm_dc': fields.String(required=True, description='The name of the DC', enum=['CTO', 'Meteor', 'Gemstone', 'Power', 'Bulk', 'Gas', 'Transversal', 'GSSNGE', 'Infra']),
  'vm_owner_gaia': fields.String(required=True, description="The owner's Gaia", pattern='^[a-zA-Z]{2}\d{4}(-(a|o)|)$'),
  'vm_resourcegroup': fields.String(required=True, description='The name of the Azure Resource Group'),
  'vm_image': fields.String(required=True, description='The name of image to use from the Resource Group'),
  'vm_os': fields.String(required=True, description='The VM Operatig System', example='Windows2016', enum=['Windows2016']),
  'vm_size': fields.String(required=True, description='The size of the Azure VM', enum=['Standard_A2_v2', 'Standard_A8_v2', 'Standard_A8m_v2', 'Standard_B8ms', 'Standard_D2_v3', 'Standard_D4_v3', 'Standard_DS12_v2', 'Standard_DS4_v2', 'Standard_DS5_v2', 'Standard_E16s_v3', 'Standard_E64is_v3', 'Standard_F16s_v2', 'Standard_F8s', 'Standard_B2ms', 'Standard_B1ms', 'Standard_B2s', 'Standard_DS13_v2', 'Standard_DS14_v2', 'Standard_D3_v2', 'Standard_DS1_v2', 'Standard_DS2_v2']),
  'vm_name': fields.String(description='The name of the VM')
})

delete_onprem_model = ns_onpremise.model('Delete a VM On Premise', {
  'vm_name': fields.String(required=True, description='The name of the VM'),
  'target_env': fields.String(required=True, description='The target environment', enum=['Development', 'Homologation', 'Production'])
})

delete_azurevm_model = ns_azure.model('Delete an Azure VM', {
  'vm_name': fields.String(required=True, description='The name of the VM'),
  'resource_group':  fields.String(required=True, description='The name of the Azure Resource Group')
})

get_onprem_model = ns_infos.model('Get job or workflow infos', {
  'wf_id': fields.Integer(required=True, description='The AWX Job Id')
})

@ns_infos.route('/<int:id>')
#@ns_onpremise.doc(params={'awx_url': 'AWX base URL', 'awx_token': 'AWX access token', 'payload': 'JSON payload'})
@ns_infos.doc(params={'id': 'AWX Job Id'})
class GetInfos(Resource):            #  Create a RESTful resource
  # @ns_onpremise.expect(get_onprem_model)
  def get(self, id):
    """
    Get infos from a job or a workflow
    """
    conf = config.readConfig()
    if conf == 1:
      logger.error('Missing configuration')
      return 'Internal Error : Missing configuration. Fix it at ' + request.url_root + 'config'
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Internal Error : Impossible to connect to AWX [' + awx_url + ']'
    
    logger.info('Getting information for the following AWX job or workflow : ' + str(id))
    return common.getAWXInfos(awx_url=awx_url, awx_token=conf['awx_token'], item_id=id)

@ns_infos.route('/stdout/<int:id>')
@ns_infos.doc(params={'id': 'AWX Job Id'})
class GetStdout(Resource):            #  Create a RESTful resource
  # @ns_onpremise.expect(get_onprem_model)
  def get(self, id):
    """
    Get the standard output from a job
    """
    conf = config.readConfig()
    if conf == 1:
      logger.error('Missing configuration')
      return 'Internal Error : Missing configuration. Fix it at ' + request.url_root + 'config'
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Internal Error : Impossible to connect to AWX [' + awx_url + ']'

    logger.info('Getting stdout for the following AWX job : ' + str(id))
    return Response(common.getAWXStdout(awx_url=awx_url, awx_token=conf['awx_token'], item_id=id), mimetype='text/plain') 

@ns_onpremise.route('/')
class OnPremise(Resource):            #  Create a RESTful resource
  @ns_onpremise.expect(create_onprem_model)
  def post(self):                     #  Create POST endpoint
    """
    Create a VM on premise on VMWare
    """
    conf = config.readConfig()
    if conf == 1:
      logger.error('Missing configuration')
      return 'Internal Error : Missing configuration. Fix it at ' + request.url_root + 'config'
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Internal Error : Impossible to connect to AWX [' + awx_url + ']'
    
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

    logger.info('Creating a VM on Premise with the following parameters : ' + dumps(payload['extra_vars']))
    return common.launchAWXItem(awx_url=awx_url, awx_token=conf['awx_token'], item_type='workflow_job_templates', item_name='Create Windows VM On Premise', payload=payload)
  
  @ns_onpremise.expect(delete_onprem_model)
  def delete(self):
    """
    Delete a VM on premise on VMWare
    """
    conf = config.readConfig()
    if conf == 1:
      logger.error('Missing configuration')
      return 'Internal Error : Missing configuration. Fix it at ' + request.url_root + 'config'
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Internal Error : Impossible to connect to AWX [' + awx_url + ']'
    
    extra_vars = {}
    payload = {}
    extra_vars['target_env'] = api.payload['target_env']
    extra_vars['vm_name'] = api.payload['vm_name']
    payload['extra_vars'] = extra_vars

    logger.info('Deleting a VM on Premise with the following parameters : ' + dumps(payload['extra_vars']))
    return common.launchAWXItem(awx_url=awx_url, awx_token=conf['awx_token'], item_type='workflow_job_templates', item_name='Delete Windows VM On Premise', payload=payload)

@ns_azure.route('/')
class Azure(Resource):            #  Create a RESTful resource
  @ns_azure.expect(create_azurevm_model)
  def post(self):                     #  Create POST endpoint
    """
    Create a VM in Azure cloud from an image
    """
    conf = config.readConfig()
    if conf == 1:
      logger.error('Missing configuration')
      return 'Internal Error : Missing configuration. Fix it at ' + request.url_root + 'config'
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Internal Error : Impossible to connect to AWX [' + awx_url + ']'
    
    extra_vars = {}
    payload = {}
    extra_vars['resource_group'] = api.payload['vm_resourcegroup']
    extra_vars['image'] = api.payload['vm_image']
    extra_vars['size'] = api.payload['vm_size']
    extra_vars['owner'] = api.payload['vm_owner_gaia']
    extra_vars['operating_system'] = api.payload['vm_os']
    extra_vars['target_dc'] = api.payload['vm_dc']
    extra_vars['vmname'] = api.payload['vm_name']
    payload['extra_vars'] = extra_vars

    logger.info('Creating an Azure VM from an image with the following parameters : ' + dumps(payload['extra_vars']))
    return common.launchAWXItem(awx_url=awx_url, awx_token=conf['awx_token'], item_type='workflow_job_templates', item_name='Create Windows VM On Azure', payload=payload)
  
  @ns_azure.expect(delete_azurevm_model)
  def delete(self):
    """
    Delete an Azure VM
    """
    conf = config.readConfig()
    if conf == 1:
      logger.error('Missing configuration')
      return 'Internal Error : Missing configuration. Fix it at ' + request.url_root + 'config'
    check_con = common.checkAWXconnection(awx_url=awx_url)
    if check_con != 200:
      return 'Internal Error : Impossible to connect to AWX [' + awx_url + ']'
    
    extra_vars = {}
    payload = {}
    extra_vars['resource_group'] = api.payload['resource_group']
    extra_vars['vm_name'] = api.payload['vm_name']
    payload['extra_vars'] = extra_vars

    logger.info('Deleting an Azure VM with the following parameters : ' + dumps(payload['extra_vars']))
    return common.launchAWXItem(awx_url=awx_url, awx_token=conf['awx_token'], item_type='job_templates', item_name='Remove azure VM', payload=payload)

@app.route('/version')
def index_version():
  return platform.python_version()

@app.errorhandler(404)
def ma_page_404(error):
  return render_template('404.html', titre="Hahaha 404, N00b !"), 404
  
if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port='5003')
