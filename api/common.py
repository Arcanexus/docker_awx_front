#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import requests

def checkAWXconnection(awx_url, awx_token):
  headers = {}
  headers['Authorization'] = "Bearer " + awx_token
  headers['Content-Type'] = "application/json"
  headers['Accept'] = "application/json"
  
  session = requests.Session()
  session.trust_env = False
  
  check_conn = session.get(awx_url + '/api/v2/workflow_job_templates/', headers=headers, verify=False)

  return check_conn.status_code