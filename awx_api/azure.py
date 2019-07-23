#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import requests
from json import dumps, loads
from flask import jsonify

def createAzureVM(awx_url, awx_token, payload):
  
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path
  
  list_wf_templates = session.get(awx_url + '/api/v2/workflow_job_templates/', headers=headers, verify=False)
  res_json=loads(list_wf_templates.content)
  output_dict = [x for x in res_json['results'] if x['name'] == 'Create Windows VM On Azure']
  create_vm_workflow_id = output_dict[0]['id']
  
  response = session.post(awx_url + '/api/v2/workflow_job_templates/' + str(create_vm_workflow_id) + '/launch/', data=dumps(payload), headers=headers, allow_redirects=True, verify=False)
  
  # get wf status
  wf_output = {}
  wf_output['id'] = response.json()['workflow_job']
  wf_output['response_code'] = response.status_code
  return wf_output

def deleteAzureVM(awx_url, awx_token, payload):
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path
  
  list_wf_templates = session.get(awx_url + '/api/v2/job_templates/', headers=headers, verify=False)
  res_json=loads(list_wf_templates.content)
  output_dict = [x for x in res_json['results'] if x['name'] == 'Remove azure VM']
  create_vm_workflow_id = output_dict[0]['id']

  response = session.post(awx_url + '/api/v2/job_templates/' + str(create_vm_workflow_id) + '/launch/', data=dumps(payload), headers=headers, allow_redirects=True, verify=False)
  
  # get wf status
  wf_output = {}
  wf_output['id'] = response.json()['job']
  if response.status_code == 201:
    wf_output['response_code'] = 204 # HTTP code for No Content
  else:
    wf_output['response_code'] = response.status_code
  return wf_output

def getAzureVMInfos(awx_url, awx_token, wf_id):
  return 'TODO'
