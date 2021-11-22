# Connection credentials to SFTP
var_prenosy = dict(host='host',username='user',password='password')
var_prenosy_test = dict(host='host',username='user',password='password')

# Connection credentials to the source database
source_db = dict(host="host", database="database", username="user", password="password")

# Files paths
dir_archive = r"archive_path"
log = r"log_path"
dir_work = r"work_path"

# Number of files I want to keep in the archive folder
pocet_archiv = 30

# Pushover notification / api and user key
pushover = dict(user_key='user_key', api_token='api')
