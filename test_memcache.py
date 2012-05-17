#!/usr/bin/python
import memcache
import string
import random
import thread
import sys

mc_couchbase1 = memcache.Client(['10.22.83.100:11222'], debug=0)
mc_couchbase2 = memcache.Client(['10.22.83.101:11222'], debug=0)
mc_couchbase3 = memcache.Client(['10.22.83.103:11222'], debug=0)
mc_couchbase4 = memcache.Client(['10.22.83.91:11222'], debug=0)

def gen_random_string(size):
    char_set = string.ascii_lowercase + string.digits
    return ''.join(random.sample(char_set,size))

def junk_to_memcache():
    while True:
#       random_number = str(random.randint(0,5))
#       random_mc = "mc_couchbase"+random_number
        key = gen_random_string(15)
        value = gen_random_string(25)
        mc_couchbase1.set(key,value)
        mc_couchbase2.set(value,key)
        mc_couchbase3.set(value,key)
        mc_couchbase4.set(key,value)
# Create two threads as follows
try:
   thread.start_new_thread(junk_to_memcache, ())
   thread.start_new_thread(junk_to_memcache, ())
   thread.start_new_thread(junk_to_memcache, ())
   thread.start_new_thread(junk_to_memcache, ())
except:
   print "Unexpected error:", sys.exc_info()

while 1:
    pass
