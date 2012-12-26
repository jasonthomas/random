#!/bin/env python
## populate /etc/puppet/autosign.conf based on tags

from boto.ec2 import connect_to_region, regions
import sys

region = 'us-west-2'
autosign = '/etc/puppet/autosign.conf'
filters = {'tag:Project': 'amo'}

try:
    conn = connect_to_region(region)
    reservations = conn.get_all_instances(filters=filters)
    private_dns = [i.private_dns_name for r in reservations for i in r.instances]

    with open(autosign, 'w') as fp:
        for i in private_dns:
            fp.write(i + '\n')
except:
    print sys.exc_info()
