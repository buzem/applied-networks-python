import socket
import os
import sys
import threading
import time
import subprocess
from random import randint
from py_essentials import hashing as hs

clear = lambda: os.system('clear')
active_users = {}
torrentable_files = {}
CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'
packetsize = 1024 * 10
thread_pool = 300

print("maximum_tcp_thread_count " + str(thread_pool))
PORT = 12345


broadcast_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){2}[0-9]*' | grep -Eo '([0-9]*\.){2}[0-9]*' | grep -v '127.0.0'")

ip_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'")

main_display_lines = ""
print(ip_address)
print_lock = threading.Lock()
file_being_downloaded = 0


active_app = 0
active_app_number = 0
messenger_target_ip = ""
messenger_target_name = ""

file_request_manager_target_ip = 0
file_request_manager_file_name = ""
file_request_manager_file_size = 0
file_being_downloaded_ip_list = []
file_being_downloaded_filepath_list = []
torrent_app_keys = []

file_requested = 0
file_requested_path = ""

used_udp_ids = []


class torrentable_file:
    def __init__(self, name, hash, size):
        self.name = name
        self.hash = hash
        self.size = size
        self.ip_addresses = {}

    def add_ip_address(self, ip_address, file_path):
        if ip_address not in self.ip_addresses:
            self.ip_addresses[ip_address] = file_path


class fileObject:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.packets = []
        self.completePackages = 0
        count = 0
        for i in range(int(size) // packetsize):
            self.packets.append([False, count, (count * packetsize), ((count + 1) * packetsize), ""])
            count = count + 1
        if int(size) % packetsize != 0:
            self.packets.append(
                [False, count, (count * packetsize), (count * packetsize) + (int(size) % packetsize), ""])

    def ifComplete(self):
        total = 0
        for i in range(len(self.packets)):
            if self.packets[i][0]:
                total = total + 1
        self.completePackages = total
        return total == len(self.packets)

    def completePercentage(self):
        return int(self.completePackages) / int(len(self.packets)) * 100


def printPacketsToAFile(fileName):
    global file_being_downloaded
    try:
        f = open(fileName, "ab")
        for i in range(len(file_being_downloaded.packets)):
            while file_being_downloaded.packets[i][0] == False:
                time.sleep(0.25)
            byt = string_interpreter(file_being_downloaded.packets[i][4][2:-1])
            file_being_downloaded.packets[i][4] = ""  # remove written bytes
            print("file write status %"+str(round(((100*i)/len(file_being_downloaded.packets)), 2)))
            sys.stdout.write(CURSOR_UP_ONE)
            sys.stdout.write(ERASE_LINE)
            f.write(byt)
        f.close()
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)
        sys.stdout.write()
        print(file_being_downloaded.name + " [%100] ")
        file_being_downloaded = 0
    except:
        pass
        # print("")


def main_display():
    while active_app_number == 1:
        sys.stdout.write(CURSOR_UP_ONE)
        clear()
        print("_________________ACTIVE USERS_________________\n          (type -torrent for torrent)          ")
        if len(active_users) >= 1:
            list_counter = 1
            for x, y in active_users.items():
                print(str(list_counter) + "_" + y + "," + x)
                list_counter += 1
        print("Which user do you want to talk to\n")
        time.sleep(0.5)


def user_choice_listener():
    global active_app_number
    global active_app
    global user_choice_string
    global messenger_target_ip
    global messenger_target_name
    global file_request_manager_target_ip
    global file_being_downloaded
    global file_request_manager_file_name
    global file_request_manager_file_size
    while True:
        user_choice_string = input()
        # main_screen displaying
        if active_app_number == 1:
            if not user_choice_string == "-torrent":
                try:
                    str_int = int(user_choice_string)


                    temp = threading.Thread(target=messenger,
                                                  args=(list(active_users.values())[int(user_choice_string) - 1],
                                                        list(active_users.keys())[int(user_choice_string) - 1],))
                    active_app_number = 2
                    active_app.join()
                    active_app = temp
                    active_app.start()
                except:
                    print("Please enter a valid number you see on the list :"+str(active_app_number))
            elif user_choice_string == "-torrent":
                active_app_number = 4
                active_app.join()
                active_app = threading.Thread(target=torrent)
                active_app.start()
        # messanger app displaying
        elif active_app_number == 2:
            sys.stdout.write(CURSOR_UP_ONE)
            sys.stdout.write(ERASE_LINE)
            if user_choice_string == "-back":
                active_app_number = 1
                active_app.join()
                active_app = threading.Thread(target=main_display)
                active_app.start()
            elif "-file" in user_choice_string:
                try:
                    stats = os.stat(str(user_choice_string.split(" ")[1]))
                    data_string = "[" + user_name + "," + str(ip_address) + ",filesendrequest," + str(
                        user_choice_string.split(" ")[1]) + "," + str(
                        user_choice_string.split(" ")[2]) + "," + str(stats.st_size) + "]"
                    send_tcp_message_over_udp(-1, messenger_target_ip, data_string, "synmessage")
                except:
                    pass
            else:
                try:
                    data_string = "[" + user_name + "," + str(ip_address) + ",message," + str(user_choice_string) + "]"
                    send_tcp_message_over_udp(-1, messenger_target_ip, data_string, "synmessage")
                    try:
                        f = open(str(messenger_target_name) + "_" + str(messenger_target_ip) + ".txt", "a+")
                        f.write(user_name + ":" + user_choice_string + "\n")
                        f.close()
                    except:
                        pass
                        # print("")
                except:
                    clear()
                    active_users.pop(messenger_target_ip)
                    print("Connection closed, User offline")
        # file downloader popup displaying
        elif active_app_number == 3:
            if file_request_manager_target_ip == 0 or user_choice_string.lower() == "yes":
                sys.stdout.write(CURSOR_UP_ONE)
                sys.stdout.write(ERASE_LINE)
                file_being_downloaded = fileObject(file_request_manager_file_name, file_request_manager_file_size)
                print("file request manager started")
                count = 0
                start = time.time()
                file_printer = threading.Thread(target=printPacketsToAFile, args=(file_being_downloaded.name,))
                file_printer.start()
                number_of_seeds = len(file_being_downloaded_filepath_list)
                for packet in file_being_downloaded.packets:
                    count += 1
                    data_string = "[" + user_name + "," + str(ip_address) + ",filerequest," + str(
                        packet[1]) + "," + str(
                        file_being_downloaded_filepath_list[(count - 1) % number_of_seeds]) + "," + str(
                        packet[2]) + "," + str(
                        packet[3]) + "]"
                    while thread_pool == 0:
                        #print("waiting for threadpool")
                        time.sleep(0.25)
                    send_tcp_message_over_udp(-1, file_being_downloaded_ip_list[(count - 1) % number_of_seeds],
                                              data_string,
                                              "synmessage")
                    sys.stdout.write(CURSOR_UP_ONE)
                    sys.stdout.write(ERASE_LINE)
                    print(file_being_downloaded.name + " [%" + str(
                        round(file_being_downloaded.completePercentage(), 2)) + "] " + str(
                        round((file_being_downloaded.completePackages * packetsize) / (
                                    1024 * (time.time() - start)),
                              2)) + " KB/s  threadpool: "+str(thread_pool))
                    file_being_downloaded.ifComplete()
                sys.stdout.write(CURSOR_UP_ONE)
                sys.stdout.write(ERASE_LINE)
                print("Finishing final writings")
                file_printer.join()
                print("file download completed. If you want to go back type -back")
                file_request_manager_target_ip = -1
                user_choice_string = "-back"
            elif user_choice_string == "-back":
                active_app_number = 1
                active_app = threading.Thread(target=main_display)
                active_app.start()
        # torrent app displaying
        elif active_app_number == 4:
            if user_choice_string == "-back":
                active_app_number = 1
                active_app.join()
                active_app = threading.Thread(target=main_display)
                active_app.start()
            else:
                try:
                    file_being_downloaded_ip_list.clear()
                    file_being_downloaded_filepath_list.clear()

                    for key2 in torrentable_files[torrent_app_keys[int(user_choice_string)]].ip_addresses:
                        file_being_downloaded_ip_list.append(key2)
                        file_being_downloaded_filepath_list.append(torrentable_files[torrent_app_keys[int(user_choice_string)]].ip_addresses[key2])
                    active_app_number = 3
                    active_app.join()
                    active_app = threading.Thread(target=file_request_manager, args=(
                        torrentable_files[torrent_app_keys[int(user_choice_string)]].name, torrentable_files[torrent_app_keys[int(user_choice_string)]].size, 0,))
                    active_app.start()


                except:
                    print("Please enter a valid number you see on the list "+str(active_app_number))


def file_sender_manager(filepath, packageid, offset1, offset2, target_ip):
    global file_requested_path
    global file_requested
    try:
        if file_requested_path != filepath:
            if file_requested_path != "":
                file_requested.close()
            file_requested = open(filepath, "r+b")
            file_requested_path = filepath
            if int(offset1) != 0:
                file_requested.seek(int(offset1))
            data = file_requested.read(int(offset2) - int(offset1))
            data_string = "[" + user_name + "," + str(ip_address) + ",filepackage," + str(packageid) + "," + str(data) + "]"
            send_tcp_message_over_udp(-1, target_ip, data_string, "synmessage")
        elif file_requested_path == filepath:
            if int(offset1) != 0:
                file_requested.seek(int(offset1))
            data = file_requested.read(int(offset2) - int(offset1))
            data_string = "[" + user_name + "," + str(ip_address) + ",filepackage," + str(packageid) + "," + str(data) + "]"
            send_tcp_message_over_udp(-1, target_ip, data_string, "synmessage")

    except FileNotFoundError:
        # not handled
        pass


def file_request_manager(name, size, target_ip):
    global file_being_downloaded
    global user_choice_string
    global file_request_manager_target_ip
    global file_request_manager_file_name
    global file_request_manager_file_size
    file_request_manager_file_name = name
    file_request_manager_file_size = size
    file_request_manager_target_ip = target_ip
    clear()
    if target_ip != 0:
        print("_____________________FILE DOWNLOAD _____________________")
        print("Do you want to receive file " + name + " from " + target_ip + " (for download type \"yes\")")
    elif target_ip == 0:
        print("Press any key to start download torrentable file")



def torrent_app_display():
    global active_app_number
    global torrent_app_keys
    clear()

    while active_app_number == 4:
        clear()
        torrent_app_keys.clear()
        torrent_app_keys.append("blank key")
        print("______________TORRENTABLE FILES IN YOUR LAN______________")
        count = 1
        for key in torrentable_files:
            print(str(count) + "-" + str(torrentable_files[key].name) + " " + str(
                torrentable_files[key].size) + " #seeds:" + str(len(torrentable_files[key].ip_addresses)))
            torrent_app_keys.append(key)
            count += 1
        time.sleep(5)


def torrent():
    global torrent_displaying
    global user_choice_string
    torrent_display = threading.Thread(target=torrent_app_display)
    torrent_display.start()


def messenger_display(filename):
    global active_app_number
    clear()
    number_of_messages = 0

    try:
        file = open(filename, "x")
    except FileExistsError:
        pass

    while active_app_number == 2:
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
    global active_app_number
    global active_app
    global messenger_target_ip
    global messenger_target_name
    messenger_target_name = target_name
    messenger_target_ip = target_ip
    active_app = threading.Thread(target=messenger_display, args=(target_name + "_" + target_ip + ".txt",))
    active_app.start()



def udp_listener():
    global ip_address
    global active_app
    global active_app_number
    UDP_IP = ""
    UDP_PORT = 12345
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, addr = sock.recvfrom(6 * packetsize)
        if data:
            # ip_address.packetid
            udp_id = str(data.decode("utf-8").rstrip(os.linesep).split("*", 2)[0])
            packetid = str(udp_id.split(".", 5)[4])
            udp_type = str(data.decode("utf-8").rstrip(os.linesep).split("*", 2)[1])
            data = data.decode("utf-8").rstrip(os.linesep).split("*", 2)[2]
            senderip = str(udp_id.split(".", 5)[0]) + "." + str(udp_id.split(".", 5)[1]) + "." + str(
                udp_id.split(".", 5)[2]) + "." + str(udp_id.split(".", 5)[3])

            if udp_id not in used_udp_ids and senderip != ip_address:
                if udp_type == "synmessage":

                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    host = senderip
                    port = 12345

                    used_udp_ids.append(udp_id)
                    name_of_the_file = data.split(",")[0][1:] + "_" + data.split(",")[1] + ".txt"
                    if data.split(",")[2] == "message":
                        try:
                            f = open(name_of_the_file, "a+")
                            f.write(data.split(",")[0][1:] + ":" +
                                    data.split(",", 3)[3][:-1] + "\n")
                            f.close()

                        except:
                            # print("file exists")
                            pass
                    elif data.split(",")[2] == "filesendrequest":
                        # incase user waits a lot to type an answer
                        s.sendto(
                            (ip_address + "." + str(packetid) + "*" + str("synackmessage") + "*" + "").encode(
                                "utf-8"),
                            (host, port))
                        file_being_downloaded_ip_list.clear()
                        file_being_downloaded_filepath_list.clear()
                        file_being_downloaded_filepath_list.append(str(data.split(",")[3]))
                        file_being_downloaded_ip_list.append(str(data.split(",")[1]))
                        active_app_number = 3
                        active_app.join()
                        active_app = threading.Thread(target=file_request_manager, args=(
                            data.split(",")[4], data.split(",")[5][:-1], data.split(",")[1],))
                        active_app.start()
                    elif data.split(",")[2] == "filerequest":
                        # print("file package sent")
                        file_sender_manager(data.split(",")[4], data.split(",")[3], data.split(",")[5],
                                            data.split(",")[6][:-1], data.split(",")[1])
                    elif data.split(",")[2] == "filepackage" and file_being_downloaded!= 0:
                        file_being_downloaded.packets[int(data.split(",")[3])][4] = data.split(",", 4)[4][:-1]
                        file_being_downloaded.packets[int(data.split(",")[3])][0] = True

                    s.sendto(
                        (ip_address + "." + str(packetid) + "*" + str("synackmessage") + "*" + "").encode(
                            "utf-8"),
                        (host, port))
                    s.close()
                elif udp_type == "synackmessage":
                    try:
                        used_udp_ids.remove(str(udp_id))
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                        host = senderip
                        port = 12345
                        s.sendto(
                            (ip_address + "." + str(packetid) + "*" + str("ackmessage") + "*" + "").encode("utf-8"),
                            (host, port))
                        s.close()
                    except:
                        pass
                elif udp_type == "ackmessage":
                    try:
                        used_udp_ids.remove(str(udp_id))
                    except:
                        print("packet doesnt even exist")

                elif udp_type == "announcetorrent":
                    for str_element in data[1:-1].split("|", 3):

                        if str_element != "":
                            if str_element.split("*")[2] not in torrentable_files:
                                torrentable_files[str_element.split("*")[2]] = torrentable_file(
                                    str_element.split("*")[0], str_element.split("*")[2], str_element.split("*")[3])
                                torrentable_files[str_element.split("*")[2]].add_ip_address(str(senderip),
                                                                                            str_element.split("*")[1])
                            else:
                                torrentable_files[str_element.split("*")[2]].add_ip_address(str(senderip),
                                                                                            str_element.split("*")[1])

                elif data.split(",")[2] == "announce]" and \
                        data.split(",")[1] != ip_address and udp_type == "announce":
                    target_ip = data.split(",")[1]
                    data_string = "[" + user_name + "," + str(ip_address) + ",response]"
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                        host = target_ip
                        port = 12345
                        data_string = str(target_ip) + ".0*response*" + data_string
                        s.sendto(data_string.encode("utf-8"), (host, port))
                        s.close()
                    except:
                        pass
                    active_users[data.split(",")[1]] = \
                        data.split(",")[0][1:]
                elif udp_type == "response":
                    # print("response received from " + data.decode("utf-8").rstrip(os.linesep).split(",")[1])
                    active_users[data.split(",")[1]] = \
                        data.split(",")[0][1:]


            else:
                if udp_type == "synmessage":
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                        host = senderip
                        port = 12345
                        s.sendto(
                            (ip_address + "." + str(packetid) + "*" + str("synackmessage") + "*" + "").encode("utf-8"),
                            (host, port))
                        s.close()
                    except:
                        # print("file exists")
                        pass
                elif udp_type == "synackmessage":
                    try:
                        used_udp_ids.remove(str(udp_id))
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                        host = senderip
                        port = 12345
                        s.sendto(
                            (ip_address + "." + str(packetid) + "*" + str("ackmessage") + "*" + "").encode("utf-8"),
                            (host, port))
                        s.close()
                    except:
                        pass
                elif udp_type == "ackmessage":
                    try:
                        used_udp_ids.remove(str(udp_id))
                    except:
                        print("packet doesnt even exist")
                pass


def activate_announcer():
    start = time.time()
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        host = '<broadcast>'
        port = 12345
        d = "./torrent_share"
        count = 0
        data_string = str(ip_address) + ".0*announcetorrent*["
        for path in os.listdir(d):
            full_path = os.path.join(d, path)
            if os.path.isfile(full_path):
                if count == 3:
                    s.sendto((data_string + "]").encode("utf-8"), (host, port))
                    data_string = str(ip_address) + ".0*announcetorrent*["
                    count = 0

                stats = os.stat(full_path)
                data_string += str(os.path.basename(full_path)) + "*" + full_path + "*" + str(
                    hs.fileChecksum(full_path, "sha256")) + "*" + str(stats.st_size) + "|"
                count += 1
        s.sendto((data_string + "]").encode("utf-8"), (host, port))
        data_string = str(ip_address) + ".0*announce*[" + user_name + "," + str(ip_address) + ",announce]"
        if time.time()-start >= 10:
            start=time.time()
            active_users.clear()
            torrentable_files.clear()
        s.sendto(data_string.encode("utf-8"), (host, port))
        time.sleep(1)


def send_tcp_message_over_udp(id, target_ip, message, messagetype):
    x = threading.Thread(target=tcp_over_udp_thread, args=(id, target_ip, message, messagetype,))
    x.start()


def tcp_over_udp_thread(id, target_ip, message, messagetype):
    global thread_pool
    thread_pool -= 1
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    host = target_ip
    port = 12345
    global used_udp_ids
    if id == -1:
        id = randint(1, 2 ** 32 - 1)
        while str(target_ip) + "." + str(id) in used_udp_ids:
            id = randint(1, 2 ** 32 - 1)
        used_udp_ids.append(str(target_ip) + "." + str(id))
    while str(target_ip) + "." + str(id) in used_udp_ids:
        s.sendto((ip_address + "." + str(id) + "*" + str(messagetype) + "*" + message).encode("utf-8"), (host, port))
        # ("tcp sent :" + message)
        time.sleep(0.25)
    s.close()
    thread_pool += 1


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


def string_interpreter(input_string):
    output_bytes = b''
    i = 0
    while i < len(input_string):
        if input_string[i] == "\\" and input_string[i + 1] == "x":
            output_bytes += (bytes.fromhex(input_string[i + 2:i + 4]))
            i = i + 4
        elif input_string[i] == "\\":
            if input_string[i + 1] == "r":
                output_bytes += bytes("\r", "utf8")
            elif input_string[i + 1] == "n":
                output_bytes += bytes("\n", "utf8")
            elif input_string[i + 1] == "t":
                output_bytes += bytes("\t", "utf8")
            elif input_string[i + 1] == "a":
                output_bytes += bytes("\a", "utf8")
            elif input_string[i + 1] == "b":
                output_bytes += bytes("\b", "utf8")
            elif input_string[i + 1] == "f":
                output_bytes += bytes("\f", "utf8")
            elif input_string[i + 1] == "\'":
                output_bytes += bytes("\'", "utf8")
            elif input_string[i + 1] == "\"":
                output_bytes += bytes("\"", "utf8")
            elif input_string[i + 1] == "\\":
                output_bytes += bytes("\\", "utf8")
            else:
                output_bytes += bytes("\\", "utf8")
            i = i + 2
        else:
            output_bytes += (input_string[i].encode("utf8"))
            i = i + 1
    return output_bytes


user_name = input()
while True:
    if "," in user_name:
        clear()
        print("Your username cannot contain ',' ")
        user_name = input()
    else:
        break

announcer = threading.Thread(target=activate_announcer)
udp_listen = threading.Thread(target=udp_listener)
active_app = threading.Thread(target=main_display)
user_choice_listener_thread = threading.Thread(target=user_choice_listener)
user_choice_listener_thread.start()
announcer.start()
active_app_number = 1
active_app.start()
udp_listen.start()
