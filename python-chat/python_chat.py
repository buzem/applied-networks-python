import socket
import os
import sys
import logging
import threading
import time
import struct
import subprocess

clear = lambda: os.system('clear')

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
    listener_thread = threading.Thread(target=user_choice_listener)
    listener_thread.start()
    try:
        f = open("active_users.txt", "x")
    except FileExistsError:
        pass
        # print("")
    while main_display_displaying:
        clear()
        print("_________________ACTIVE USERS_________________")
        try:
            f = open("active_users.txt", "r+")
            global main_display_lines

            main_display_lines = f.read().splitlines()

            if len(main_display_lines) >= 1:
                for i in range(1, len(main_display_lines) + 1):
                    print(str(i) + "_" + main_display_lines[i - 1])
            f.close()
            time.sleep(3)
        except:
            pass
            # print("")


def user_choice_listener():
    global main_display_displaying
    user_input = input("Which user do you want to talk to")
    main_display_displaying = False
    try:
        messenger(main_display_lines[int(user_input) - 1].split(",")[0],
                  main_display_lines[int(user_input) - 1].split(",")[1])
    except ValueError:
        print("please enter a number")


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
        except:
            pass
        #  print("error in reading the message file ")
        time.sleep(3)


def messenger(target_name, target_ip):
    display_messages = threading.Thread(target=messenger_display, args=(target_name + "_" + target_ip + ".txt",))
    display_messages.start()
    while True:
        user_input = input()
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)
        if user_input == "-back":
            global messenger_displaying
            global main_display_displaying
            messenger_displaying = False
            main_display_displaying = True
            display_messages.join()
            active_users = threading.Thread(target=main_display)
            active_users.start()
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
                s.shutdown(2)
                s.close()


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


def activate_announcer():
    try:
        f = open("active_users.txt", "x")
    except FileExistsError:
        pass
        #print("file exists")
    while True:
        f = open("active_users.txt", "w+")
        f.write("")
        for i in range(1, 254):
            if i != int(str(ip_address).split(".")[3]):
                x = threading.Thread(target=send_broadcast_message, args=(i,))
                x.start()
                # sockets[i].connect(( str(broadcast_address)+"."+str(i), 12345))

        time.sleep(20)


def handle_message(conn, addr):
    # data received from client
    data = conn.recv(1024)
    if data:
        # print(data.decode("utf-8"))

        if data.decode("utf-8").rstrip(os.linesep).split(",")[2] == "announce]":
            target_ip = data.decode("utf-8").rstrip(os.linesep).split(",")[1]
            # print(target_ip)
            # print("sent before")
            data_string = "[" + user_name + "," + str(ip_address) + ",response]"
            x = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            x.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            x.connect((str(target_ip), 12345))
            x.sendto(data_string.encode("utf-8"), (str(target_ip), 12345))
            x.shutdown(2)
            x.close()
            try:
                active_users_file = open("active_users.txt", "r+")
                if not "{0},{1}".format(
                        data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:],
                        data.decode("utf-8").rstrip(os.linesep).split(",")[1]) in active_users_file.read():
                    # print("i wrote")
                    active_users_file.write(data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:] + "," +
                                            data.decode("utf-8").rstrip(os.linesep).split(",")[1] + "\n")
                    active_users_file.close()
            except IOError:
                pass
        elif data.decode("utf-8").rstrip(os.linesep).split(",")[2] == "response]":
            # print("response received from " + data.decode("utf-8").rstrip(os.linesep).split(",")[1])
            try:
                active_users_file = open("active_users.txt", "r+")
                if not "{0},{1}".format(
                        data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:],
                        data.decode("utf-8").rstrip(os.linesep).split(",")[1]) in active_users_file.read():
                    # print("i wrote")
                    active_users_file.write(data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:] + "," +
                                            data.decode("utf-8").rstrip(os.linesep).split(",")[1] + "\n")
                    active_users_file.close()
            except IOError:
                pass
        elif data.decode("utf-8").rstrip(os.linesep).split(",")[2] == "message":
            name_of_the_file = data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:] + "_" + \
                               data.decode("utf-8").rstrip(os.linesep).split(",")[1] + ".txt"
            try:
                f = open(name_of_the_file, "a+")
                f.write(data.decode("utf-8").rstrip(os.linesep).split(",")[0][1:] + ":" + data.decode("utf-8").rstrip(os.linesep).split(",")[3][:-1] + "\n")
                f.close()
            except:
                # print("file exists")
                pass

    print_lock.release()
    conn.close()


def activate_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip_address, 12345))
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
announcer = threading.Thread(target=activate_announcer)
listener = threading.Thread(target=activate_listener)
monitor = threading.Thread(target=main_display)
announcer.start()
listener.start()
monitor.start()
