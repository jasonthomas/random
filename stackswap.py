#!/bin/env python
# swap out cloudformation stacks attached to a specific elb

import boto.ec2.elb
import boto.ec2
import boto.cloudformation
import time
import sys
import json
from optparse import OptionParser


# This will cause full debug output to go to the console
#boto.set_stream_logger('foo')

# returns a list of ec2 instance ids attached to a lb
def get_instance_ids(elbname, conn):
    instance_ids = []

    for instance in conn.describe_instance_health(elbname):
        instance_ids.append(instance.instance_id)

    return instance_ids


# return a list of ec2 instances belonging to stack_id
def get_stack_instance_ids(stack_id, conn):
    filters = {'tag:aws:cloudformation:stack-id': stack_id}

    return [i.id for i in conn.get_only_instances(filters=filters)]


# if instances is a list, pass it to describe_instance_health
def get_instance_health(elbname, conn, instances=None):
    instance_states = []

    for instance in conn.describe_instance_health(elbname):
        instance_states.append(instance.state)

    return instance_states


# returns a list of ec2 stacknames
def get_instance_stackname(instance_ids, conn):
    tagname = 'aws:cloudformation:stack-name'
    return [i.tags[tagname]
        for i in conn.get_only_instances(instance_ids=instance_ids)]


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
def check_elb_health(elbname, conn, instances=None, sleep=30):
    elapsed = 0
    while not is_healthy(get_instance_health(elbname, conn, instances)):
        print "waiting on health..."
        time.sleep(sleep)
        elapsed += sleep
        # wait 15 minutes, if not bail
        if elapsed >= 900:
            print "elb failed to be healthy"
            return False
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


def stack_wait(stack_id, conn):
    start = time.time()
    while (time.time() - start) < 900:
        stack = conn.describe_stacks(stack_id)[0]
        if stack.stack_status != 'CREATE_IN_PROGRESS':
            return stack.stack_status
        time.sleep(30)

    return 'TIMED_OUT'


def main():
    parser = OptionParser(usage="usage: %prog [options] stack_name elb_name template_file") # flake8: noqa
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

    STACKNAME = args[0]
    ELBNAME = args[1]
    STACKTEMPLATE = args[2]

    elb = boto.ec2.elb.ELBConnection()
    ec2 = boto.ec2.connection.EC2Connection()
    cloud = boto.cloudformation.connection.CloudFormationConnection(debug=0)

    # get instances associated with a elb
    instances = get_instance_ids(ELBNAME, elb)

    # get the current stack name
    current_stack_name = check_equal(get_instance_stackname(instances, ec2))

    # check to see if multiple stacks are associated with the the elb
    # we should bail if there is as there should always only be one
    if current_stack_name is not False:
        # create the new stack
        stack_id, stack_name = create_stack(STACKNAME, STACKTEMPLATE, cloud)
        print "building new stack: %s" % stack_name

        # Wait for stack creation to complete.
        state = stack_wait(stack_id, cloud)
        if state != 'CREATE_COMPLETE':
            print "new stack creation failed with state: %s" % state
            sys.exit(1)

        # check the health of instances attached to the elb
        # once this returns True we can delete the previous stack
        new_instances = get_stack_instance_ids(stack_id, ec2)
        if check_elb_health(ELBNAME, elb, instances=new_instances):
            print "new stack is ready: %s" % stack_name

            cloud.delete_stack(current_stack_name)
            print "deleting previous stack: %s" % current_stack_name

            sys.exit(0)

        else:
            print "new stack failed. deleting: %s" % stack_name
            cloud.delete_stack(stack_name)
            sys.exit(1)

    else:
        print 'Multiple stacks attached to ELB. Is this okay?'
        sys.exit(1)


if __name__ == '__main__':
    main()
