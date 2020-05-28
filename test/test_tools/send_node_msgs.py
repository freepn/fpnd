import time

from nanoservice import Requester


# addr = '127.0.0.1'
addr = '192.168.0.66'

id_list = [
              'deadbeef00', 'deadbeef04', 'deadbeef03', 'deadbeef02', 'deadbeef01'
              'deadbeef00', 'deadbeef04', 'deadbeef03', 'deadbeef02', 'deadbeef01'
              'deadbeef00', 'deadbeef04', 'deadbeef03', 'deadbeef02', 'deadbeef01'
              'deadbeef00', 'deadbeef04', 'deadbeef03', 'deadbeef02', 'deadbeef01'
              'deadbeef00', 'deadbeef04', 'deadbeef03', 'deadbeef02', 'deadbeef01'
          ]

# Need to wait a bit to prevent lost messages
# time.sleep(0.001)


def echo_client(fpn_id, addr, call_func=None):

    if not call_func:
        call_func = 'echo'

    reply_list = []
    reciept = False
    c = Requester('tcp://{}:9443'.format(addr), timeouts=(1000, 1000))

    try:
        reply_list = c.call(call_func, fpn_id)
        reciept = True
        if call_func == 'echo':
            print(reply_list)
    except Exception as exc:
        print('Send error is {}'.format(exc))
        raise exc

    return reply_list, reciept


for node_id in id_list:
    result = echo_client(node_id, addr)
    # result = echo_client(node_id, addr, call_func='node_cfg')
    print('Sent request msg {} to {}'.format(node_id, addr))
    print('Got result: {}'.format(result))
