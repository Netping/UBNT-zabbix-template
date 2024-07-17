#!/usr/bin/env python3
"""
Import XML configuration files using Zabbix API:
https://www.zabbix.com/documentation/3.4/manual/api/reference/configuration/import
"""
import argparse
from urllib import request
import json
import sys
from pprint import pformat
import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def zbxrequest(url, method, auth, params):

    if params is None:
        params = {}
    data = { "jsonrpc": "2.0", "id": 1, "method": method, "auth": auth, "params": params }
    # Convert to string and then to byte
    data = json.dumps(data).encode('utf-8')
    req = request.Request(args.url, headers={'Content-Type': 'application/json-rpc'}, data=data)
    resp = request.urlopen(req)
    # Get string
    resp = resp.read().decode('utf-8')
    # Convert to object
    resp = json.loads(resp, encoding='utf-8')
    return resp


try:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Import XML configuration files using Zabbix API')
    parser.add_argument('-u', '--user', required=True, help='user name')
    parser.add_argument('-p', '--password', '--pass', required=True, help='password', metavar='PASSWORD')
    parser.add_argument('-s', '--url', default='http://127.0.0.1:80/api_jsonrpc.php',
                        help='Zabbix API URL, default is http://127.0.0.1:80/api_jsonrpc.php')
    args = parser.parse_args()

    # TODO: add API version check
    # r=zbxrequest(args.url, method="apiinfo.version", auth=None, params={})
    # print(r)

    # Get authentication token
    # https://www.zabbix.com/documentation/3.4/manual/api/reference/user/login
    auth_result = zbxrequest(args.url, method="user.login", auth=None,
                             params={"username": args.user, "password": args.password})

    # If authentication was not OK
    if 'result' not in auth_result:
        raise Exception('ERROR: auth failed\n' + pformat(auth_result))

    auth_token = auth_result['result']

    # Read template file content
    #with open(args.template_file, 'r', encoding='utf-8') as f:
    #    source = f.read()

    # Set import parameters, including template file content
    params = {
               "output": [ "mediatypeid" ],
               "filter": { "name": "Send SMS (via Internal NetPing)" }
             }

    # https://www.zabbix.com/documentation/3.4/manual/api/reference/configuration/import
    get_result = zbxrequest(args.url, method="mediatype.get", auth=auth_token, params=params)
    # Something like: {'id': 1, 'jsonrpc': '2.0', 'result': True}

    if 'result' in get_result and get_result['result']:
        print('SUCCESS: mediatype get')
    else:
        raise Exception('ERROR: mediatype get failed\n' + pformat(get_result))

    mediatypeid = get_result['result'][0]['mediatypeid']

    params = {
               "userid": "1",
               "medias": [
                 {
                   "mediatypeid": mediatypeid,
                   "sendto": "+70000000000",
                   "active": "0",
                   "period": "1-7,00:00-24:00",
                   "severity": "63"
                 }
               ]
             }

    update_result = zbxrequest(args.url, method="user.update", auth=auth_token, params=params)

    if 'result' in update_result and update_result['result']:
        print('SUCCESS: user update')
    else:
        raise Exception('ERROR: user update failed\n' + pformat(update_result))

    params = {
               "output": [ "hostid" ],
               "filter": {
                 "host": [ "Internal_NetPing" ]
               }
             }

    get_result = zbxrequest(args.url, method="host.get", auth=auth_token, params=params)

    if 'result' in get_result and get_result['result']:
        print('SUCCESS: host get')
    else:
        raise Exception('ERROR: host get failed\n' + pformat(get_result))

    hostid = get_result['result'][0]['hostid']

    params = {
               "name": "Report By SMS",
               "eventsource": 0,
               "filter": {
                 "evaltype": 0,
                 "conditions": [
                   {
                     "conditiontype": 1,
                     "operator": 0,
                     "value": hostid
                   }
                 ]
               },
               "operations": [
                 {
                   "operationtype": 0,
                   "opmessage_grp": [
                     {
                       "usrgrpid": "7"
                     }
                   ],
                   "opmessage": {
                     "default_msg": 1,
                     "mediatypeid": mediatypeid
                   }
                 }
               ]
             }

    create_result = zbxrequest(args.url, method="action.create", auth=auth_token, params=params)

    if 'result' in create_result and create_result['result']:
        print('SUCCESS: action create')
    else:
        raise Exception('ERROR: action create failed\n' + pformat(create_result))

    exit_code = 0

except Exception as e:

   print(str(e), file=sys.stderr)
   exit_code=1

finally:
    # Logout to prevent generation of unnecessary open sessions
    # https://www.zabbix.com/documentation/3.4/manual/api/reference/user/logout
    if 'auth_token' in vars():
        zbxrequest(args.url, method="user.logout", auth=auth_token, params={})
