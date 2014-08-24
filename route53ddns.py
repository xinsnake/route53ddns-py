#!/usr/local/bin/python3

import logging
import time
import urllib3
import boto.route53

start_time = time.time()

# configuration
cfg_profile = 'Credential'
cfg_region = 'us-east-1'
cfg_zone = 'YOUR.DOMAIN'
cfg_record = 'A.YOUR.DOMAIN'
cfg_timeout = 300
aws_key = 'YOUR AWS KEY'
aws_secret = 'YOUR_AWS_SECRET'

# set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address = '/dev/log')
formatter = logging.Formatter('%(module)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

# get ip address
http = urllib3.PoolManager()
request = http.request('GET', 'http://curlmyip.com')
ip_addr = request.data.decode("utf-8")[:-1]

log.info('Current IP address: ' + ip_addr)

# check current ip address
conn = boto.route53.connect_to_region(
    cfg_region,
    aws_access_key_id = aws_key,
    aws_secret_access_key = aws_secret
)
zone = conn.get_zone(cfg_zone)
a_record = zone.get_a(cfg_record)
a_record_value = a_record.resource_records[0]

log.info('Route53 DNS record address: %s' % a_record_value)

# check whether it's the same
if ip_addr != a_record_value:
    # needs update
    log.warning('IP Changed, update needed.')
    status = zone.update_a(cfg_record, ip_addr)
    log.info('Record updated, waiting to sync, timeout in %s seconds' % str(cfg_timeout))
    # check for status update
    count = 0
    while (count < cfg_timeout):
        count = count + 1
        time.sleep(1)
        status.update()
        if status.status == 'INSYNC':
            log.info('Record synced, exit')
            break
        if count == cfg_timeout:
            log.error('Sync timeout, exit')
else:
    # should be fine
    log.info('No need to update, exit.')

log.info('Total time spent: %s seconds' % str(round(time.time() - start_time, 4)))