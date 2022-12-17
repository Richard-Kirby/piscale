import socket
from datetime import datetime, timedelta

UDP_IP = "255.255.255.255"
UDP_PORT = 6000

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

last_msg_received_time = None
while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    now = datetime.now()
    result = str(data).split(',')
    weight = float(result[1][:-1].strip())

    if last_msg_received_time == None:
        last_msg_received_time = now
        print(f"received message:{now}, {data}, {result}, {weight}")
    else:
        time_diff = now-last_msg_received_time
        #print(time_diff)

        if time_diff > timedelta(minutes=1):
            print("new measurement")
            last_msg_received_time = now
            print(f"received message:{now}, {data}, {result}, {weight}")
