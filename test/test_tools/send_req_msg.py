import time

from nanoservice import Requester


addr = '127.0.0.1'
# addr = 'whatever'

c = Requester('tcp://{}:9443'.format(addr), timeouts=(1000, 1000))
id_list = ['deadbeef00', 'deadbeef04', 'deadbeef03', 'deadbeef02', 'deadbeef01']

# Need to wait a bit to prevent lost messages
time.sleep(0.001)


for node_id in id_list:
    reply_list = c.call('echo', node_id)
    print('Sent request msg {} to {}'.format(node_id, addr))
    print('Got result: {}'.format(reply_list))
