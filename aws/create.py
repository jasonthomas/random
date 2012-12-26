#!/bin/env python

import boto.ec2
import os

eu = boto.ec2.regions()[4]
ec2 = eu.connect()

def get_instance_by_tags(filters=None):
    return ec2.get_all_instances(filters=filters)

def create_instances(image_id='ami-2a31bf1a', 
                     key_name='jthomas',
                     security_groups=None,
                     count=1, tags=None, subnet_id=None):

    counter = 0
    while (counter < count): 
        reservation = ec2.run_instances(image_id, key_name=key_name,
                                        security_groups=security_groups,
                                        subnet_id=subnet_id) 
        instance = reservation.instances[0]
        print instance
    
        if not tags is None:
            for key, value in tags.iteritems():
                instance.add_tag(key, value)
                
        counter = counter + 1


#filters = {'tag:Name': 'solitude.admin'}
#some=get_instance_by_tags(filters)
#for r in some:
#    print r.instances[0]
#filters = {'tag:Project':'amo', 'tag:Type':'admin'}

tags = {
        'Name':'solitude-rabbitmq',
        'Type':'rabbitmq',
        'Project':'amo',
        'App':'solitude',
        }

private_tags = {
        'Name':'solitude-vpc-private',
        'Type':'private',
        'Project':'amo',
        'App':'vpc',
        }

public_tags = {
        'Name':'solitude-vpc-public',
        'Type':'public',
        'Project':'amo',
        'App':'vpc',
        }
 
private_subnet = 'subnet-615b3208'
public_subnet = 'subnet-655b320c'
#create_instances(tags=tags)
#create_instances(tags=private_tags, subnet_id=private_subnet)
create_instances(tags=public_tags, subnet_id=public_subnet)
