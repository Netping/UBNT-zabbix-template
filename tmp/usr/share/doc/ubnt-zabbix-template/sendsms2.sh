#!/bin/bash
curl --user visor:ping --data "[$1] $2" http://192.168.0.100/sendsms.cgi?utf8