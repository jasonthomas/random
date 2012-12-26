#!/bin/env python
## return yaml based tags

from boto.ec2 import connect_to_region, regions
import sys
import yaml

region = 'us-west-2'
#filters = {'tag:Project': 'amo'}
aws_access_key_id = ''
aws_secret_access_key = ''
fqdn = sys.argv[1]
filters = {'tag:Project': 'amo',
           'private_dns_name': fqdn,
          }

def get_type(filters):
    try:
        conn = connect_to_region(region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        reservations = conn.get_all_instances(filters=filters)
        if not reservations:
            sys.exit('Host not found')
        else:
            return reservations[0].instances[0].__dict__['tags']['Type']
    except:
        print sys.exc_info()

def create_yaml(tag):  
    tclass = "base::%s" % tag
    pclass =  tclass.encode('ascii','ignore')
    data = {"classes": [pclass,'something'] }
             
    print yaml.dump(data, default_flow_style=False, indent=10)



tag=get_type(filters)
create_yaml(tag)

