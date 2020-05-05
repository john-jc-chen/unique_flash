import serial_rx_tx
import time
import sys
import time
import re
import os
import logging

import _thread

logFile = None
write_able = False

username = "ADMIN"
passwd = "ADMIN"
new_passwd = ''
comport = ""
baudrate = "9600"
bootloader = ""
firmware = ""
IP = ''
config_file = sys.argv[1]
commands = ''
set_default = True
serial_number = ''
with open(config_file, 'r') as f:
    commands = f.readlines()
    for comm in commands:
        if comm.startswith("COM Port:"):
            comport = comm[9:].rstrip()
        elif comm.startswith("Baud Rate:"):
            baudrate = comm[10:].rstrip()
        else:
            pass
#f.close()
serialPort = serial_rx_tx.SerialPort()

def OnReceiveSerialData():
    time.sleep(1.0)
    while serialPort.serialport.in_waiting > 0:
        print(serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8"))
        time.sleep(1.0)
def OpenCommand():
    global comport
    global baudrate
    serialPort.Open(comport,baudrate)
    print("COM Port Opened\r\n")

def login(username, passwd):
    serialPort.Send("")
    serialPort.Send("")
    time.sleep(10.0)
    serialPort.Send_raw(" ")
    time.sleep(0.2)
    serialPort.Send(username)
    #time.sleep(1.0)
    OnReceiveSerialData()
    serialPort.Send(passwd)
    time.sleep(1.0)
    message = serialPort.serialport.read(serialPort.serialport.inWaiting())
    try:
        data = message.decode("utf-8")
        print(data)
        if "SMIS#" not in data:
            print("Failed to login with the password \"" + passwd + "\"\n Leave scrip!!!")
            serialPort.Close()
            sys.exit()
    except:
        pass
    #data = serialPort.serialport.read(serialPort.serialport.inWaiting())
    #print(data)

def logout():
    str = "exit\r"
    serialPort.serialport.write(str.encode("utf-8"))
    time.sleep(1.0)

def write_log(message):
    if os.name == 'posix':
        log_dir = os.getcwd() + '/log'
    else:
        log_dir = os.getcwd() + "\\log"
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    serial= '123'
    if os.name == 'posix':
        file_name =log_dir + '/' + serial_number
    else:
        file_name =log_dir + "\\" + serial_number
    logging.basicConfig(filename=file_name,level=logging.INFO, format='%(asctime)s - %(message)s', datefmt = '%d-%b-%y %H-%M-%S')
    logging.info(message)

def set_factory_default():
    while True:
        time.sleep(2.0)
        message = ''
        if serialPort.serialport.in_waiting > 0:
            message = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8", errors='ignore')
        #message = serialPort.serialport.readline().decode("utf-8", errors='ignore')
        print(message)
        if " Boot Menu " in message:
            time.sleep(1.0)
            serialPort.Send_raw(" ")
            time.sleep(1.0)
            serialPort.Send_raw('p')
            print(serialPort.serialport.readline().decode("utf-8", errors='ignore'))
            serialPort.Send('y')
            break

OpenCommand()

if serialPort.IsOpen():
    #serialPort.Send("")
    upgrad_firmware = True
    login_with_new_pwd = False
    msg = ''
    while True:
        #time.sleep(1.0)
        #print(serialPort.serialport.in_waiting, upgrad_firmware)
        if serialPort.serialport.in_waiting > 0:
        #if message:
            #message = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8")
            message = serialPort.serialport.readline().decode("utf-8", errors='ignore')
            print(message)
            #of.write(message)
            message = message.rstrip()
            m = re.findall(r"serial\=(\w+)$", message)
            if m:
                serial_number = m[0]
            #msg = msg + message
            if " login:" in message:
                #OnReceiveSerialData()
                if upgrad_firmware:
                    start_time = time.time()
                    with open(config_file, 'r') as f:
                    #f = open(config_file, 'r')
                        commands = f.readlines()
                        i = 0
                        for comm in commands:
                            if comm.startswith("User Name:"):
                                username = comm[10:].rstrip()
                            elif comm.startswith("New Password:"):
                                new_passwd = comm[13:].rstrip()
                                # commands[i]="New Password:\n"
                            elif comm.startswith("TFTP:"):
                                TFTP = comm[5:].rstrip()
                            elif comm.startswith("Firmware Name:"):
                                firmware = comm[14:].rstrip()
                            elif comm.startswith("Bootloader Name:"):
                                bootloader = ''
                                bootloader = comm[16:].rstrip().lstrip()
                            elif comm.startswith("Set Factory Default:"):
                                m = re.findall(r"^Set\s+Factory\s+Default:\s?(\w+).*", comm)
                                if m:
                                    ans = m[0]
                                    if ans.lower() == 'no':
                                        set_default= False
                                   # print(comm)
                            else:
                                pass
                            i += 1
                    #f.close()
                    if new_passwd == '':
                        print("ERROR!! Please write unique password in the configuration file!\n Leave script!!!")
                        serialPort.Close()
                        sys.exit()
                    elif len(new_passwd) != 10:
                        print("ERROR!! New password is not composed with 10 characters!\n Leave script!!!")
                        serialPort.Close()
                        sys.exit()
                    login(username, 'ADMIN')
                    time.sleep(1.0)
                    OnReceiveSerialData()
                    if bootloader != "":
                        serialPort.Send('upgrade bootloader tftp://' + TFTP + '/' + bootloader + ' normal')
                    time.sleep(1.0)
                    while serialPort.serialport.in_waiting > 0:
                        message = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8")
                        print(message)
                        if "SMIS#" in message:
                            break
                        time.sleep(2.0)

                    serialPort.Send('firmware upgrade tftp://' + TFTP + '/' + firmware + ' normal')
                    time.sleep(1.0)
                    while True:
                        message = serialPort.serialport.readline().decode("utf-8", errors='ignore')
                        print(message)
                        if "SMIS#" in message:
                            break
                        elif 'upgrade?' in message:
                            serialPort.Send('y')
                        elif 'successfully' in message:
                            serialPort.Send('')
                    serialPort.Send('reload')
                    time.sleep(1.0)
                    OnReceiveSerialData()
                    serialPort.Send_raw('y')
                    msg = ''
                    upgrad_firmware = False
                else:
                    if not login_with_new_pwd:
                        if new_passwd == '':
                            print("ERROR!! New password is blank!\n Leave script!!!")
                            serialPort.Close()
                            sys.exit()
                        elif len(new_passwd) != 10:
                            print("ERROR!! New password is not composed with 10 characters!\n Leave script!!!")
                            serialPort.Close()
                            sys.exit()
                        login(username, 'ADMIN')
                        serialPort.Send("configure terminal")
                        time.sleep(1.0)
                        OnReceiveSerialData()
                        serialPort.Send("factory-unique-password " + new_passwd)
                        time.sleep(1.0)
                        OnReceiveSerialData()
                        serialPort.Send_raw('y')
                        serialPort.Send("exit")
                        time.sleep(0.5)
                        OnReceiveSerialData()
                        serialPort.Send('reload')
                        time.sleep(1.0)
                        OnReceiveSerialData()
                        serialPort.Send_raw('y')
                        login_with_new_pwd = True
                        msg = ''
                        if set_default:
                            set_factory_default()
                    else:
                        login(username, new_passwd)
                        serialPort.Send("show version")
                        time.sleep(1.0)
                        message = ''
                        while serialPort.serialport.in_waiting > 0:
                            message += serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8")
                            time.sleep(1.0)
                        print(message)
                        f = open(config_file, 'w')
                        for comm in commands:
                            if comm.startswith("New Password:"):
                                f.write("New Password:\n")
                            else:
                                f.write(comm)
                        f.close()
                        write_log(message)
                        upgrad_firmware = True
                        new_passwd = ''
                        login_with_new_pwd = False
                        msg = ''
                        set_default = True
                        serial_number = ''
                        print("\nUpdate Finshed!\nTotal time: %s seconds" % (time.time() - start_time))
                        #input("Update Finshed! Press enter to continue")

            elif message.endswith("=>"):
                upgrad_firmware = True
                login_with_new_pwd = False
                com = input()
                serialPort.Send(com)
                while True:
                    if com == "bootmenu":
                        break
                    while serialPort.serialport.in_waiting:
                        print(serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8"))
                    com = input()
                    serialPort.Send(com)
else:
    print("Not sent - COM port is closed\r\n")
