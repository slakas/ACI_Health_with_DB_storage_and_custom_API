#!/bin/sh
#run mysql
service mysql start
script='/mnt/run_ACI_health.py'
/usr/bin/python3 $script &
