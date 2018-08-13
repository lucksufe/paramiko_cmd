import sys
import os
import paramiko
import time
import thread

FULL_WORKER_TABLE = []
FULL_CMD_TABLE = []
RESERVED_ADDRESS = []
JTL_IP_PREFIX = '172.21.232.'
FULL_WORKER_FEEDBACK = {}
batch_count = 0


def add_ip(arr):
    for num in arr:
        if num in RESERVED_ADDRESS:
            continue
        FULL_WORKER_TABLE.append(JTL_IP_PREFIX + str(num))


def add_jtl_full_ip(filt=1):
    arr = []
    for num in range(15, 249):
        if num % filt == 0:
            arr.append(num)
    add_ip(arr)


def add_hd_second_ip():
    hd_table = ['182.01.01.01', '182.01.01.01', '182.01.01.01', '182.01.01.01']
    FULL_WORKER_TABLE.extend(hd_table)


def baidu_nameserver():
    cmds = ['echo \'nameserver 172.16.48.2\'>>/etc/resolv.conf',
            'echo \'nameserver 172.16.32.2\'>>/etc/resolv.conf',
            'echo \'nameserver 172.16.32.3\'>>/etc/resolv.conf',
            'ldconfig']
    FULL_CMD_TABLE.extend(cmds)
    execute_cmd()


def shut_down_renderer(need_execute=True):
    FULL_CMD_TABLE.append('ps aux|grep Start.py|awk \'{print $2}\'|xargs kill -9')
    FULL_CMD_TABLE.append('ps aux|grep pawner|awk \'{print $2}\'|xargs kill -9')
    if need_execute:
        execute_cmd(False)


def start_renderer():
    shut_down_renderer(False)
    FULL_CMD_TABLE.append('./start_SMP')
    execute_cmd(False)


def execute_cmd_batch(pty=True, sleep=0, batch_num=10):
    limit = len(FULL_WORKER_TABLE)
    pointer = 0
    while pointer < limit:
        pointer += batch_num
        thread.start_new_thread(execute_cmd, (pty, sleep, FULL_WORKER_TABLE[pointer:pointer+10 > limit and limit or pointer+10], True))
    while batch_count > 0:
        time.sleep(10)
    del FULL_CMD_TABLE[:]


def execute_cmd(pty=True, sleep=0, work_list=FULL_WORKER_TABLE, is_batch=False):
    global batch_count
    if is_batch:
        batch_count += 1
    for ip_address in work_list:
        time.sleep(sleep)
        print ('exec_command at ' + ip_address)
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        info = generate_info(ip_address)
        try:
            s.connect(hostname=ip_address, port=22, username=info[0], password=info[1])
            for cmd in FULL_CMD_TABLE:
                stdin, stdout, stderr = s.exec_command(cmd, get_pty=pty)
                print('cmd :'+cmd)
                if 'sudo' in cmd:
                    stdin.write(info[1] + '\n')
                for line in stdout:
                    FULL_WORKER_FEEDBACK[ip_address] = FULL_WORKER_FEEDBACK.get(ip_address,'') + line.strip('\n')
                    print(line.strip('\n')) 
                for line in stderr:
                    print(line.strip('\n')) 
                time.sleep(1)
            s.close()
        except Exception as e:
            print('fail at '+ip_address)
            print(e)
    if is_batch:
        batch_count -= 1
    else:
        del FULL_CMD_TABLE[:]


def send_file(filenames, src_dir, remote_dir):
    for ip_address in FULL_WORKER_TABLE:
        print ('copying to ' + ip_address)
        info = generate_info(ip_address)
        try:
            transport = paramiko.Transport((ip_address, 22))
            transport.connect(username=info[0], password=info[1])
            sftp = paramiko.SFTPClient.from_transport(transport)
            i = 0
            while i < len(filenames):
                src_dir2 = os.path.join(src_dir, filenames[i])
                dst_dir = os.path.join(remote_dir, filenames[i])
                print(src_dir2, dst_dir)
                sftp.put(src_dir2, dst_dir)
                mode = os.stat(src_dir2).st_mode
                sftp.chmod(dst_dir, mode)
                i += 1
            sftp.close()
        except Exception as e:
            print('fail at '+ip_address)
            print(e)


def send_dir(ip_address, src_dir, remote_dir, local_prefix):
    print ('copying to ' + ip_address)
    local_dir = os.path.join(local_prefix, src_dir)
    info = generate_info(ip_address)
    try:
        transport = paramiko.Transport((ip_address, 22))
        transport.connect(username=info[0], password=info[1])
        sftp = paramiko.SFTPClient.from_transport(transport)
        for root, dirs, files in os.walk(local_dir):
            root = root[len(local_prefix) + 1:]
            sftp.mkdir(os.path.join(remote_dir, root))
            for file_name in files:
                src_dir = os.path.join(local_prefix, root, file_name)
                dst_dir = os.path.join(remote_dir, root, file_name)
                sftp.put(src_dir, dst_dir)
                mode = os.stat(src_dir).st_mode
                sftp.chmod(dst_dir, mode)
                print('send', src_dir, dst_dir)
        sftp.close()
    except Exception as e:
        print('fail at ' + ip_address)
        print(e)


def generate_info(ip_address):
    return ['username', 'password']


if __name__ == '__main__':
    
    sys.exit(0)

