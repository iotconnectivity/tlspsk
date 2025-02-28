from os import sep
import socket
import time
from tlspsk import TLSClientSession
from datetime import datetime, timedelta, timezone

from credentials import psk, iccid

def main():

    quit = False
    sock = None

    server = '34.253.244.76'
    port = 11111
    # server = "127.0.0.1"
    # port = 443

    def callback(data):
        nonlocal quit, sock
        print(data)
        if data == b"bye\n":
            quit = True

    session = TLSClientSession(
        server_names=server, psk=psk, psk_label=iccid, data_callback=callback, psk_only=True
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server, port))
    client_hello = session.pack_client_hello()
    print('client hello: {0}'.format(client_hello.hex()))
    sock.sendall(client_hello)

    parser = session.parser()
    step = 0
    while not quit:
        step += 1
        server_data = sock.recv(10*4096)
        if len(server_data) > 0:
            print("step {0}: {1}".format(step, server_data.hex()))
        parser.send(server_data)
        data = parser.read()
        if data:
            print("data: {0}".format(data.hex()))
            sock.sendall(data)
            quit = True

    dt = datetime.utcnow()
    stime = dt.strftime('%y/%m/%d %H:%M:%S UTC')

    # iot pushing telemetry data with POST
    data_string = '{"temperature": 36.70}'
    data = bytes('POST /v1/data/51523143572089723527?iccid={0} HTTP/1.1\x0d\x0a'.format(iccid.hex()) +
                 'Host: pod.iot.platform\x0d\x0a' +
                 'Content-Length: {0}\x0d\x0a\x0d\x0a{1}'.format(len(data_string), data_string), 'utf-8')

    # iot getting config data with GET
    # data = bytes('GET /v1/config/51523143572089723526?iccid=984405529081369836f5 HTTP/1.1\x0d\x0a' +
    #              '\x0d\x0a', 'utf-8')

    print('request: {0}'.format(data))
    app_data = session.pack_application_data(data)
    print('app_data: {0}'.format(app_data.hex()))

    sock.sendall(app_data)
    time.sleep(1)
    resp = sock.recv(4096)
    print('resp: {0}'.format(resp.hex()))
    parser.send(resp)

    time.sleep(0.5)
    resp = sock.recv(4096)
    print('resp: {0}'.format(resp.hex()))
    parser.send(resp)

    sock.sendall(session.pack_close())
    sock.close()
    print('done!')


main()
