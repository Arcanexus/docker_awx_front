from json import dumps, loads, dump, load
from awx_api import common

def readConfig():
  try:
      with open("config.json", 'r') as json_file:
        return load(json_file)
  except FileNotFoundError:
    return 1

def writeConfig(awx_token):
  config={}
  config['awx_token'] = awx_token
  try: 
    with open('config.json', 'w') as outfile:
      dump(config, outfile)
  except FileNotFoundError:
    return 1


