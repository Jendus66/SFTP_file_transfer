# SFTP_file_transfer

The short Python script for getting data from the source database, appending them to file and transfer this file via SFTP. <br>
Run of the script is logged into file log.txt.<br>
If some exception occurs during the run, script sends a notification to smartphone via Pushover app.<br>
The script does these actions:
1) Get credentials for the connection of source database, SFTP, keys for Pushover app etc. from config.py file
2) Get data from the source database
3) Create a file for transfer and append the data
4) Connection to SFTP and transfer the file
5) Copy the file to the archive folder and delete the oldest file from the folder
