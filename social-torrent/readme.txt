This program is tested on MacOSX 10.15 Catalina and (2x)Ubuntu 18.04.2 LTS(VBox) on my LAN.

You should setİ:
"ulimit -n 1024" or higher in order not to get too many open files error on Mac because it is set to a small number in default.

When program first starts, it shows current IP address and you are required to type
An alias for yourself and then the program starts functioning.

If you want to go back from open message window, type "-back". Then you will be redirected
To the "Active Users" window.

If you want to go see what files are shared in your LAN, type "-torrent". Then you will be redirected to the "Torrent" app where you can see and download shared files. You can see how many seeds there are of that file. Choose the file number and follow instructions. You will see the download process on the screen as well. If you want the app to share a file you should create a directory named "torrent_share" at the same location as the application code.

If you want to send a file directly to a user, you have to use messanger app first. Choose the user from "Active Users" list. Follow this format:
 -file file path future_file_name_on_receiving_end
Then approve request on the other end. File mustn't exist on the receiving destination otherwise, application just appends on the existing file which damages the file :)



