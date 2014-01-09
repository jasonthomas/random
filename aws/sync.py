#!/bin/env python
# sync a directory to s3 using multiple workers

import boto
import hashlib
import os
import sys
import multiprocessing
from socket import error as socket_error

BUCKET_NAME = ''
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
WORKERS = 12
SRC_DIR = ''

queue = multiprocessing.JoinableQueue()


class Sync(multiprocessing.Process):
    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.public = False
        self.conn = self.build_connection()
        self.bucket = self.conn.get_bucket(BUCKET_NAME)
        from boto.s3.key import Key
        self.k = Key(self.bucket)

    def build_connection(self):
        return boto.connect_s3(AWS_ACCESS_KEY_ID,
                               AWS_SECRET_ACCESS_KEY)

    def run(self):
        while not queue.empty():
            print queue.qsize()
            filename = self.queue.get()
            self.k.key = os.path.relpath(filename, SRC_DIR)
            s3key = self.bucket.get_key(self.k.key)
            if s3key:
                etag = s3key.etag.strip('"') or None
                if self.md5sum(filename) != etag:
                    self.upload(filename)
                    self.queue.task_done()
            else:
                self.upload(filename)
                self.queue.task_done()

    def md5sum(self, filename, blocksize=1024*1024):
        md5 = hashlib.md5()
        file = open(filename)
        while True:
            data = file.read(blocksize)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()

    def upload(self, filename):
        try:
            self.k.set_contents_from_filename(filename)
            if self.public:
                self.bucket.set_acl('public-read', self.k.key)
            print "Uploaded: %s" % filename
        except socket_error as serr:
            print 'Socket Error', serr
        except:
            print "Unexpected error:", sys.exc_info()[0]


def main():
    for path, dir, files in os.walk(SRC_DIR):
        for file in files:
            queue.put(os.path.join(path, file))

    # create workers
    workers = [Sync(queue) for i in range(WORKERS)]

    # start workers
    for w in workers:
        w.start()

    # wait till queue is empty
    while not queue.empty():
        pass

    # end workers
    for w in workers:
        w.join()


if __name__ == '__main__':
    main()
