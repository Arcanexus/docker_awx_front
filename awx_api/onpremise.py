#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import requests
from json import dumps, loads
from flask import jsonify

def createVMOnPremise(awx_url, awx_token, payload):
  
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path
  
  list_wf_templates = session.get(awx_url + '/api/v2/workflow_job_templates/', headers=headers, verify=False)
  res_json=loads(list_wf_templates.content)
  output_dict = [x for x in res_json['results'] if x['name'] == 'Create Windows VM On Premise']
  create_vm_workflow_id = output_dict[0]['id']
  
  response = session.post(awx_url + '/api/v2/workflow_job_templates/' + str(create_vm_workflow_id) + '/launch/', data=dumps(payload), headers=headers, allow_redirects=True, verify=False)
  
  # get wf status
  wf_output = {}
  wf_output['id'] = response.json()['workflow_job']
  wf_output['response_code'] = response.status_code
  return wf_output

def deleteVMOnPremise(awx_url, awx_token, payload):
  
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path
  
  list_wf_templates = session.get(awx_url + '/api/v2/workflow_job_templates/', headers=headers, verify=False)
  res_json=loads(list_wf_templates.content)
  output_dict = [x for x in res_json['results'] if x['name'] == 'Delete Windows VM On Premise']
  create_vm_workflow_id = output_dict[0]['id']

  response = session.post(awx_url + '/api/v2/workflow_job_templates/' + str(create_vm_workflow_id) + '/launch/', data=dumps(payload), headers=headers, allow_redirects=True, verify=False)
  
  # get wf status
  wf_output = {}
  wf_output['id'] = response.json()['workflow_job']
  if response.status_code == 201:
    wf_output['response_code'] = 204 # HTTP code for No Content
  else:
    wf_output['response_code'] = response.status_code
  return wf_output

def getVMOnPremiseInfos(awx_url, awx_token, wf_id):
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path  
  
  # Check if wf_id is a valid Create on prem WF
  check_wf_id = session.get(awx_url + '/api/v2/workflow_jobs/' + str(wf_id) + '/', headers=headers, verify=False)
  if check_wf_id.status_code != 200:
    return "The id " + str(wf_id) + " is not a valid workflow id."

  response = session.get(awx_url + '/api/v2/workflow_jobs/' + str(wf_id) + '/', headers=headers, allow_redirects=True, verify=False)
  
  wf_output = {}
  wf_output['id'] = response.json()['id']
  wf_output['created'] = response.json()['created']
  wf_output['status'] = response.json()['status']
  wf_output['failed'] = response.json()['failed']
  
  wf_jobs = {}
  postinstall_job_url = ''

  # Get Post Install Windows job id
  list_wf_nodes = session.get(awx_url + response.json()['related']['workflow_nodes'], headers=headers, allow_redirects=True, verify=False)
  res_json=loads(list_wf_nodes.content)
  for item in res_json['results']:
    if 'job' in item['summary_fields']:
      wf_jobs[item['summary_fields']['job']['name']] = item['summary_fields']['job']['status']
      if item['summary_fields']['job']['name'] == 'Post Install Windows':
        postinstall_job_url = awx_url + '/api/v2/jobs/' + str(item['summary_fields']['job']['id'])

  wf_output['jobs'] = wf_jobs

  if postinstall_job_url != '':
    # Get Post Install Windows job extra vars
    post_install_extravars = session.get(postinstall_job_url, headers=headers, allow_redirects=True, verify=False)
    res_json=loads(post_install_extravars.content)['extra_vars']
    vm_infos = {}
    vm_infos['name'] = loads(res_json)['vm_name']
    vm_infos['ip'] = loads(res_json)['netbox']['ip_address']
    wf_output['vm_infos'] = vm_infos
    
  return wf_output