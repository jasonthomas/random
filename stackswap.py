#!/bin/env python
# swap out cloudformation stacks attached to a specific elb

import boto.ec2.elb
import boto.ec2
import boto.cloudformation
import re
import time
import sys
import json
from optparse import OptionParser
from ConfigParser import SafeConfigParser


# This will cause full debug output to go to the console
#boto.set_stream_logger('foo')

# config file should be ini format
def configure(config_file, env):
    config = {}
    conf = SafeConfigParser()

    if conf.read(config_file):
        config['key'] = conf.get(env, 'key')
        config['secret'] = conf.get(env, 'secret')
    else:
        print 'No configuration found'

    return config


# returns a list of ec2 instance ids attached to a lb
def get_instance_ids(elbname, conn):
    instance_ids = []

    for instance in conn.describe_instance_health(elbname):
        instance_ids.append(instance.instance_id)

    return instance_ids


def get_instance_health(elbname, conn):
    instance_states = []

    for instance in conn.describe_instance_health(elbname):
        instance_states.append(instance.state)

    return instance_states


# returns a list of ec2 stacknames
def get_instance_stackname(instance_ids, conn):
    tagname = 'aws:cloudformation:stack-name'
    stack_names = []
    for reservation in conn.get_all_reservations(instance_ids=instance_ids):
        for instance in reservation.instances:
            stack_names.append(instance.tags[tagname])

    return stack_names


# checks list to see if values are identical
def check_equal(iterator):
    if len(set(iterator)) <= 1:
        return iterator[0]
    else:
        return False


# check to see if status has any healthy instances
def is_healthy(status):
    s = set(status)
    if 'OutOfService' in s:
        return False
    elif 'InService' in s and len(s) <= 1:
        return True


# busy spin to check if elb is healthy
def check_elb_health(elbname, conn):
    while not is_healthy(get_instance_health(elbname, conn)):
        print "waiting on health..."
        time.sleep(30)
    print "all instances healthy"
    return True


def create_stack(stack_name, template_file, conn, parameters=None):
    with open(template_file) as tmpfile:
        template_body = json.dumps(json.load(tmpfile))

    stack_name = "%s-%s" % (stack_name,
                            time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    try:
        result = conn.create_stack(stack_name, template_body=template_body,
                                   capabilities=['CAPABILITY_IAM'])
        return [result, stack_name]
    except Exception, e:
        print e


def main():
    parser = OptionParser(usage="usage: %prog [options] stack_name elb_name template_file")
    parser.add_option("-c", "--conf",
                      default='/etc/aws',
                      type='string',
                      help="AWS Credentials")
    parser.add_option("-r", "--region",
                      default='us-east-1',
                      type='string',
                      help="AWS region. Default is us-east-1")
    parser.add_option("-e", "--environment",
                      default='stage',
                      type='string',
                      help="Environment")

    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.error("wrong number of arguments")

    config = configure(options.conf, options.environment)

    KEY = config['key']
    SECRET = config['secret']
    STACKNAME = args[0]
    ELBNAME = args[1]
    STACKTEMPLATE = args[2]

    elb = boto.ec2.elb.ELBConnection(aws_access_key_id=KEY,aws_secret_access_key=SECRET)
    ec2 = boto.ec2.connection.EC2Connection(aws_access_key_id=KEY, aws_secret_access_key=SECRET)
    cloud = boto.cloudformation.connection.CloudFormationConnection(aws_access_key_id=KEY, aws_secret_access_key=SECRET, debug=0)

    # get instances associated with a elb
    instances = get_instance_ids(ELBNAME, elb)

    # get the current stack name
    current_stack_name = check_equal(get_instance_stackname(instances, ec2))

    # check to see if multiple stacks are associated with the the elb
    # we should bail if there is as there should always only be one
    if current_stack_name is not False:
        # create the new stack
        output = create_stack(STACKNAME, STACKTEMPLATE, cloud)
        print "building new stack: %s" % output[1]

        # sleep for a little bit while stack ec2 instances are coming up
        print "sleeping for 300 seconds"
        time.sleep(300)

        # check the health of instances attached to the elb
        # once this returns True we can delete the previous stack
        if check_elb_health(ELBNAME, elb):
            print "new stack is ready: %s" % output[1]

            cloud.delete_stack(current_stack_name)
            print "deleting previous stack: %s" % current_stack_name

        #current_stack_name = check_equal(get_instance_stackname(instances))

        # sleep
        #time.sleep(120)

        # verify that there is only one stack

        sys.exit(0)
    else:
        print 'Multiple stacks attached to ELB. Is this okay?'
        sys.exit(1)


if __name__ == '__main__':
    main()
