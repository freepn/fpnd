import time

from nanoservice import Publisher


pub_id = Publisher('tcp://127.0.0.1:9442')
id_list = ['deadbeef00', 'deadbeef04', 'deadbeef03', 'deadbeef02', 'deadbeef01']

# Need to wait a bit to prevent lost messages
time.sleep(0.001)


for node_id in id_list:
    pub_id.publish('handle_node', node_id)
    print('Published msg {}'.format(node_id))
