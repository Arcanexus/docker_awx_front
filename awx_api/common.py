#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import requests
from json import dumps, loads

def checkAWXconnection(awx_url, awx_token):
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path
  
  check_conn = session.get(awx_url + '/api/v2/workflow_job_templates/', headers=headers, verify=False)

  return check_conn.status_code

def getAWXInfos(awx_url, awx_token, wf_id):
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False #disable proxy
  session.verify = False # set SSL CA path  
  
  wf_output = {}

  # Check if wf_id is a valid workflow or job id
  check_wf_id = session.get(awx_url + '/api/v2/workflow_jobs/' + str(wf_id) + '/', headers=headers)
  check_job_id = session.get(awx_url + '/api/v2/jobs/' + str(wf_id) + '/', headers=headers)
  
  if check_wf_id.status_code != 200 and check_job_id.status_code != 200:
    return "The id " + str(wf_id) + " is not a valid job or workflow id."

  if check_wf_id.status_code == 200:
    response = session.get(awx_url + '/api/v2/workflow_jobs/' + str(wf_id) + '/', headers=headers, allow_redirects=True)

    wf_output['name'] = response.json()['name']
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

  elif check_job_id.status_code == 200:
    response = session.get(awx_url + '/api/v2/jobs/' + str(wf_id) + '/', headers=headers, allow_redirects=True)
    wf_output['name'] = response.json()['summary_fields']['job_template']['name']
    
  wf_output['id'] = response.json()['id']
  wf_output['created'] = response.json()['created']
  wf_output['status'] = response.json()['status']
  wf_output['failed'] = response.json()['failed']
  wf_output['extra_vars'] = loads(response.json()['extra_vars'])
  
  return wf_output