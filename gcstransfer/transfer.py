import googleapiclient.discovery
import json
import sys

from datetime import datetime


def create_transfer_client():
    return googleapiclient.discovery.build('storagetransfer', 'v1')


def create_transfer_job(description, project_id, year, month, day, hours,
                        minutes, source_bucket, access_key, secret_access_key,
                        sink_bucket, include_prefixes=None):
    storagetransfer = create_transfer_client()

    # Edit this template with desired parameters.
    # Specify times below using US Pacific Time Zone.
    transfer_job = {
        'description': description,
        'status': 'ENABLED',
        'projectId': project_id,
        'schedule': {
            'scheduleStartDate': {
                'day': day,
                'month': month,
                'year': year
            },
            'scheduleEndDate': {
                'day': day,
                'month': month,
                'year': year
            },
        },
        'transferSpec': {
            'awsS3DataSource': {
                'bucketName': source_bucket,
                'awsAccessKey': {
                    'accessKeyId': access_key,
                    'secretAccessKey': secret_access_key
                }
            },
            'objectConditions': {
                'includePrefixes': include_prefixes,
            },
            'gcsDataSink': {
                'bucketName': sink_bucket
            },
            'transferOptions': {
                'deleteObjectsUniqueInSink': True,
            },
        }
    }

    result = storagetransfer.transferJobs().create(body=transfer_job).execute()
    print('Returned transferJob: {}'.format(json.dumps(result, indent=4)))


def create_job():
    includes = []

    now = datetime.now()

    if len(sys.argv) < 2:
        print('Missing config prefix parameter')

    config = sys.argv[1]

    with open('%s_datasets' % config) as f:
        for include in f.readlines():
            includes.append(include.strip())

    with open('%s.json' % config) as f:
        job = json.load(f)

    job['description'] = '%s -> %s' % (job['source_bucket'],
                                       job['sink_bucket'])
    job['include_prefixes'] = includes
    job['day'] = now.day
    job['month'] = now.month
    job['year'] = now.year
    job['hours'] = now.hour
    job['minutes'] = now.minute

    create_transfer_job(**job)


create_job()
