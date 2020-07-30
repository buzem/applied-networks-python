import socket
import os
import sys
import logging
import threading
import time
import struct
import subprocess

clear = lambda: os.system('clear')
active_users = {}
CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'
PORT = 12345
broadcast_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){2}[0-9]*' | grep -Eo '([0-9]*\.){2}[0-9]*' | grep -v '127.0.0'")
ip_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'")
# sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for i in range(254)]
messenger_displaying = False
main_display_displaying = True
main_display_lines = ""
print(ip_address)
print_lock = threading.Lock()


def main_display():
    user_choice_listener_thread = threading.Thread(target=user_choice_listener)
    user_choice_listener_thread.start()
    global main_display_displaying
    main_display_displaying = True
    while main_display_displaying:
        clear()
        print("_________________ACTIVE USERS_________________")
        if len(active_users) >= 1:
            list_counter = 1
            for x, y in active_users.items():
                print(str(list_counter) + "_" + y + "," + x)
                list_counter += 1
        print("Which user do you want to talk to\n")
        time.sleep(3)
    user_choice_listener_thread.join()


def user_choice_listener():
    global main_display_displaying

    successful = False
    while not successful:
        try:
            user_input = input()
            main_display_displaying = False
            successful = True
            messenger_app = threading.Thread(target=messenger, args=(list(active_users.values())[int(user_input) - 1],
                                                                     list(active_users.keys())[int(user_input) - 1],))
            messenger_app.start()

        except:
            print("Please enter a valid number you see on the list")
            main_display_displaying = True
            successful = False
            pass


def messenger_display(filename):
    global messenger_displaying
    clear()
    messenger_displaying = True
    number_of_messages = 0

    try:
        file = open(filename, "x")
    except FileExistsError:
        pass
    # print("file exists")

    while messenger_displaying:
        try:
            file = open(filename, "r+")
            contents = file.read().splitlines()
            if len(contents) > number_of_messages:
                for i in range(number_of_messages, len(contents)):
                    print(contents[i])
                number_of_messages = len(contents)
            file.close()
            time.sleep(0.25)
        except:
            pass
        #  print("error in reading the message file ")


def messenger(target_name, target_ip):
    display_messages = threading.Thread(target=messenger_display, args=(target_name + "_" + target_ip + ".txt",))
    display_messages.start()
    global messenger_displaying
    global main_display_displaying
    while True:
        user_input = input()
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)
        if user_input == "-back":
            break
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            try:
                data_string = "[" + user_name + "," + str(ip_address) + ",message," + str(user_input) + "]"
                s.connect((target_ip, 12345))
                s.sendto(data_string.encode("utf-8"),
                         (target_ip, 12345))
                s.shutdown(2)
                s.close()

                try:
                    f = open(str(target_name) + "_" + str(target_ip) + ".txt", "a+")
                    f.write(user_name + ":" + user_input + "\n")
                    f.close()
                except:
                    pass
                    # print("")
            except:
                try:
                    s.shutdown(2)
                    s.close()
                except:
                    s.close()
                    pass
                clear()
                active_users.pop(target_ip)
                print("Connection closed, User offline")
                break
    messenger_displaying = False
    display_messages.join()
    monitor = threading.Thread(target=main_display)
    monitor.start()


def send_broadcast_message(last_digit_of_ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))

    try:
        s.connect((str(broadcast_address) + "." + str(last_digit_of_ip), 12345))
        data_string = "[" + user_name + "," + str(ip_address) + ",announce]"
        s.sendto(data_string.encode("utf-8"),
                 (str(broadcast_address) + "." + str(last_digit_of_ip), 12345))
        # print(str(broadcast_address) + "." + str(last_digit_of_ip) + " is successful!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        s.shutdown(2)
        s.close()
    except socket.error:
        # print(str(broadcast_address) + "." + str(last_digit_of_ip) + " is closed")
        s.close()


def udp_listener():
    UDP_IP = ""
    UDP_PORT = 12345
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, addr = sock.recvfrom(1500)  # buffer size is 1500 bytes
        if data:

            if data.decode("utf-8").rstrip(os.linesep).split(",")[2] == "announce]" and \
                    data.decode("utf-8").rstrip(os.linesep).split(",")[1] != ip_address:
                target_ip = data.decode("utf-8").rstrip(os.linesep).split(",")[1]
                data_string = "[" + user_name + "," + str(ip_address) + ",response]"
                try:
                    x = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    x.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                    x.connect((str(target_ip), 12345))
                    x.sendto(data_string.encode("utf-8"), (str(target_ip), 12345))
                    x.shutdown(2)
                    x.close()
                except:
                    pass
                active_users[data.decode("utf-8").rstrip(os.linesep).split(",")[1]] = data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:]


def activate_announcer():
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        host = '<broadcast>'
        port = 12345
        data_string = "[" + user_name + "," + str(ip_address) + ",announce]"
        s.sendto(data_string.encode("utf-8"), (host, port))
        s.sendto(data_string.encode("utf-8"), (host, port))
        s.sendto(data_string.encode("utf-8"), (host, port))
        time.sleep(15)


def handle_message(conn, addr):
    # data received from client
    data = conn.recv(1024)
    if data:
        # print(data.decode("utf-8"))

        if data.decode("utf-8").rstrip(os.linesep).split(",")[2] == "response]":
            # print("response received from " + data.decode("utf-8").rstrip(os.linesep).split(",")[1])
            active_users[data.decode("utf-8").rstrip(os.linesep).split(",")[1]] = \
                data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:]

        elif data.decode("utf-8").rstrip(os.linesep).split(",")[2] == "message":
            name_of_the_file = data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:] + "_" + \
                               data.decode("utf-8").rstrip(os.linesep).split(",")[1] + ".txt"
            try:
                f = open(name_of_the_file, "a+")
                f.write(data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:] + ":" +
                        data.decode("utf-8").rstrip(os.linesep).split(",", 3)[3][:-1] + "\n")
                f.close()
            except:
                # print("file exists")
                pass

    print_lock.release()
    conn.close()


def activate_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 12345))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    s.listen(5)
    while True:
        # print('listening on', (ip_address, 12345))
        conn, addr = s.accept()
        if conn:
            # print('Connected by', addr)
            print_lock.acquire()
            l = threading.Thread(target=handle_message, args=(conn, addr,))
            l.start()
            l.join()


user_name = input()
while True:
    if "," in user_name:
        clear()
        print("Your username cannot contain ',' ")
        user_name = input()
    else:
        break
announcer = threading.Thread(target=activate_announcer)
port_listener = threading.Thread(target=activate_listener)
udp_listen = threading.Thread(target=udp_listener)
monitor = threading.Thread(target=main_display)
announcer.start()
port_listener.start()
monitor.start()
udp_listen.start()
