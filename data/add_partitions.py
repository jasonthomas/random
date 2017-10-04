import boto3
from collections import defaultdict


def define_partition(config):
    partitions = defaultdict()
    s3 = boto3.client('s3', region_name=config['Region'])
    paginator = s3.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket=config['Bucket'],
                                       Prefix=config['Prefix'])
    for page in page_iterator:
        for obj in page['Contents']:
            k = obj['Key'].split('/')[0:5]
            path = '/'.join(k)
            if path not in partitions:
                day = k[3].rpartition('=')[2]
                hour = k[4].rpartition('=')[2]

                partitions[path] = [day, hour]

    return partitions


def create_partitions(config, partitions):
    glue = boto3.client('glue', region_name=config['Region'])
    current = glue.get_partitions(DatabaseName=config['DatabaseName'],
                                  TableName=config['TableName']
                                  )

    current_partitions = defaultdict()
    for c in current['Partitions']:
        current_partitions['-'.join(c['Values'])] = 1

    for path, partval in partitions.items():
        if '-'.join(partval) not in current_partitions:
            storage_descriptor = current['Partitions'][0]['StorageDescriptor']
            storage_descriptor['Location'] = 's3://%s/%s/' % (config['Bucket'],
                                                              path)
            try:
                partition_input = {
                    'Values': partval,
                    'StorageDescriptor': storage_descriptor
                }
                glue.create_partition(DatabaseName=config['DatabaseName'],
                                      TableName=config['TableName'],
                                      PartitionInput=partition_input
                                      )
                print('Added Partition %s to %s.%s' % (partval,
                                                       config['DatabaseName'],
                                                       config['TableName']))
            except:
                print('sadness')


def lambda_handler(event, context):
    for config in event:
        partitions = define_partition(config)
        create_partitions(config, partitions)
