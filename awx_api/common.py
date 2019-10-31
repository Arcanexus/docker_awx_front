#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import requests, sys
from json import dumps, loads
from flask import request
from awx_api import config

def checkAWXconnection(awx_url):
  """
  Check the connection to AWX 
  """
  conf = config.readConfig()
  if conf == 1:
    awx_token = ''
  else:
    awx_token = conf['awx_token']
  
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path
  
  check_conn = session.get(awx_url + '/api/v2/workflow_job_templates/', headers=headers, verify=False)

  check_conn_output = {}
  check_conn_output['status_code'] = check_conn.status_code
  check_conn_output['reason'] = check_conn.reason
  return check_conn_output

def getAWXInfos(awx_url, awx_token, item_id):
  """
  Retrieve information about a Job or a Workflow id 
  """
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path  
  
  item_output = {}

  # Check if item_id is a valid workflow or job id
  check_wf_id = session.get(awx_url + '/api/v2/workflow_jobs/' + str(item_id) + '/', headers=headers)
  check_job_id = session.get(awx_url + '/api/v2/jobs/' + str(item_id) + '/', headers=headers)
  
  if check_wf_id.status_code != 200 and check_job_id.status_code != 200:
    return "The id " + str(item_id) + " is not a valid job or workflow id."

  if check_wf_id.status_code == 200:
    response = session.get(awx_url + '/api/v2/workflow_jobs/' + str(item_id) + '/', headers=headers, allow_redirects=True)

    item_output['name'] = response.json()['name']
    wf_jobs = {}
    postinstall_job_url = ''

    # Get Post Install Windows job id
    list_wf_nodes = session.get(awx_url + response.json()['related']['workflow_nodes'], headers=headers, allow_redirects=True, verify=False)
    res_json=loads(list_wf_nodes.content)
    for item in res_json['results']:
      if 'job' in item['summary_fields']:
        wf_jobs[item['summary_fields']['job']['name']] = {}
        wf_jobs[item['summary_fields']['job']['name']]['id'] = item['summary_fields']['job']['id']
        wf_jobs[item['summary_fields']['job']['name']]['status'] = item['summary_fields']['job']['status']
        wf_jobs[item['summary_fields']['job']['name']]['stdout'] = request.url_root + 'api/v1/infos/stdout/' + str(item['summary_fields']['job']['id'])

        if item['summary_fields']['job']['name'] == 'Post Install Windows':
          postinstall_job_url = awx_url + '/api/v2/jobs/' + str(item['summary_fields']['job']['id'])

    item_output['jobs'] = wf_jobs

    if postinstall_job_url != '':
      # Get Post Install Windows job extra vars
      post_install_extravars = session.get(postinstall_job_url, headers=headers, allow_redirects=True, verify=False)
      res_json=loads(post_install_extravars.content)['extra_vars']
      vm_infos = {}
      vm_infos['name'] = loads(res_json)['vm_name']
      vm_infos['ip'] = loads(res_json)['netbox']['ip_address']
      item_output['vm_infos'] = vm_infos

  elif check_job_id.status_code == 200:
    response = session.get(awx_url + '/api/v2/jobs/' + str(item_id) + '/', headers=headers, allow_redirects=True)
    item_output['name'] = response.json()['summary_fields']['job_template']['name']
    item_output['stdout'] = request.url_root + 'api/v1/infos/stdout/' + str(item_id)

  item_output['id'] = response.json()['id']
  item_output['created'] = response.json()['created']
  item_output['status'] = response.json()['status']
  item_output['failed'] = response.json()['failed']
  item_output['extra_vars'] = loads(response.json()['extra_vars'])
  
  return item_output

def launchAWXItem(awx_url, awx_token, item_type, item_name , payload):
  """
  Launch a job template or a workflow template 
  """
  if item_type not in ['job_templates', 'workflow_job_templates']:
    sys.exit("Invalid item_type provided to launchAWXItem : "+item_type)

  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path
  
  list_item_templates = session.get(awx_url + '/api/v2/'+ item_type + '/', headers=headers, verify=False)
  res_json=loads(list_item_templates.content)
  output_dict = [x for x in res_json['results'] if x['name'] == item_name]
  item_id = output_dict[0]['id']
  
  response = session.post(awx_url + '/api/v2/'+ item_type + '/' + str(item_id) + '/launch/', data=dumps(payload), headers=headers, allow_redirects=True, verify=False)
  
  item_output = {}
  if response.status_code == 400:
    item_output['error'] = 'Error 400 : ' + response.reason + ' - ' + response.text
  else: # get item status
    item_output['id'] = response.json()['workflow_job']
    item_output['response_code'] = response.status_code
  return item_output

def getAWXStdout(awx_url, awx_token, item_id):
  """
  Retrieve the output of a Job id 
  """
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path
  
  # check id is a job
  check_job_id = session.get(awx_url + '/api/v2/jobs/' + str(item_id) + '/', headers=headers)
  
  if check_job_id.status_code != 200:
    return "The id " + str(item_id) + " is not a valid job id."
  
  response = session.get(awx_url + '/api/v2/jobs/' + str(item_id) + '/stdout/', headers=headers, allow_redirects=True)
  job_stdout = response.json()['content']
  
  return job_stdout #.replace('\n','<br />')

