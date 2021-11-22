import pyodbc # modul na připojení do MS SQL databáze
from datetime import datetime # modul pro datum a čas
import os # modul pro práci v systému (vytváření složek atd.)
import shutil # pro kopírování souborů
import pysftp # pro připojení pomocí sftp
from pysftp import AuthenticationException
from pysftp import SSHException
import logging # pro logování kroků programu
import sys # pro sys.exit(), pokud program spadne
import config

def db_get_data(sql):
    """Database connection (MSSQL). Input: select query, Return: table data, table header"""
    global server, database, username, password
    try:
        db_con = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server};SERVER='+server+\
                            ';DATABASE='+database+';UID='+username+';PWD='+ password)
        cursor = db_con.cursor()
        logging.info(f"Pripojeni do databaze {database} uspesne.")
        print("Spojení na db úspěšné")
        cursor.execute(sql)
        data = cursor.fetchall()
        nazvy_sloupcu = []
        for i in range(0,len(data[0])):
            nazvy_sloupcu.append(cursor.description[i][0])
        logging.info("Data nactena do pameti.")
        print("Data načtena")
        db_con.close()
        logging.info(f"Spojeni s DB {database} ukonceno.")
        print("Spojení na db ukončeno")
        return data, nazvy_sloupcu
    except Exception as e:
        logging.info(e)
        logging.info("Program ukoncen.")
        send_notification()
        print(e)
        sys.exit()

def directory_check(path, number_of_files):
    """Deleting specific number of files in a folder. Input: path (folder for delete), number_of_files (number of files I want to keep).
    """
    files = os.listdir(path)
    if len(files) > number_of_files:
        index_to_delete = -1
        oldest_date = None
        for i, file in enumerate(files):
            if i == 0:
                oldest_date = os.path.getctime(f"{archive_path}\{file}")
                index_to_delete = 0
            else:
                raw_date_creation = os.path.getctime(f"{archive_path}\{file}")
                if raw_date_creation - oldest_date < 0:
                    oldest_date = raw_date_creation
                    index_to_delete = i
        logging.info(f"Soubor smazan -> {str(files[index_to_delete])}")  
        print("Mažu soubor", files[index_to_delete])

        os.remove(f"{archive_path}\{files[index_to_delete]}")
        directory_check(path, number_of_files)

def send_notification():
    """Sending a notification to smartphone via Pushover app if an exception occurs."""
    from pushover import Client
    user_id = config.pushover['user_key']
    api_token = config.pushover['api_token']
    client = Client(user_id, api_token = api_token)
    client.send_message("Prenos z DB na SFTP neprobehl.", title="prenos")
    logging.info('Notifikace odeslána.')


# Connection to the source database 
server = config.source_db['host']
database = config.source_db['database']
username = config.source_db['username']
password = config.source_db['password']

# Connection to SFTP folder
myHostname = config.var_prenosy['host']
myUsername = config.var_prenosy['username']
myPassword = config.var_prenosy['password']

# Config of files for the program
log_path = config.log
work_path = config.dir_work
archive_path = config.dir_archive

# SQL query for the source database
sql_query = """SELECT [NAME]
,[GIVENNAME]
,[SURNAME]
,[EMPLOYEENUMBER]
,[Stat3]
,CONVERT(VARCHAR(8),[STARTDATE],112)
,CONVERT(VARCHAR(8),[ENDDATE],112)
,[KOKRS]
,[STATE]
FROM [IAM_OPERREPORTS].[dbo].[ACTUAL_PERSON]
WHERE [IS_TECHNICAL]= 0 and [STATE]='ENABLED'"""

logging.basicConfig(filename = log_path, level = logging.INFO, format = '%(asctime)s:%(levelname)s:%(message)s')
logging.info("#######################################")
logging.info("Spusteni programu.")

# Name of the final file -> YYYYMMDD.txt
file_name = datetime.today().strftime('%Y%m%d') + ".txt"

# Getting the data from the source database
data, head = db_get_data(sql_query)

# Creating the final file and appending the data from the source database (encode: utf-8, separator: tabulator)
os.chdir(work_path)
with open(file=file_name, mode='w+', encoding='utf-8') as f:
    f.write("\t".join(head) + "\n")
    for row in data:
        f.write("\t".join(str(record) for record in row) + "\n")
    logging.info(f"Soubor {file_name} vytvoren.")

# Connection to SFTP folder
try:
    with pysftp.Connection(host=myHostname, username=myUsername, password=myPassword) as sftp:
        logging.info(f"Pripojení na server {myHostname} uspesne ... ")
        print("Prihlaseni na /var/prenosy uspesne.")
        # Transfering the final file to the SFTP folder
        sftp.put(f'{work_path}\{file_name}', f'/HR/IAM/iam_sap.txt')
        logging.info("Soubor iam_sap.txt prenesen na /var/prenosy.")
        print("Soubor transportován.")
        # Creating the archive folder if does not exist
        if not os.path.exists(archive_path):
            os.mkdir(archive_path)
        # Transfering the final file from work folder to archive folder
        shutil.move(f"{work_path}\{file_name}", f"{archive_path}\{file_name}")
        logging.info(f"Soubor {file_name} presunut do archivu.")

except AuthenticationException:
    # Exception for incorrect login or password
    logging.info("Chyba v prihlaseni na server SAP.")
    logging.info("Program ukoncen s chybou.")
    send_notification()
    sys.exit()

except FileNotFoundError:
    # Exception for file was not found
    logging.info("Soubor k prenosu nenalezen.")
    logging.info("Program ukoncen s chybou.")
    send_notification()
    sys.exit()
except SSHException:
    # Exception for SSH error - occured because of bad version of pysftp library
    logging.info("Nutna aktualizace klicu mezi servery. Pridej klic do souboru known_hosts.")
    logging.info("Program ukoncen s chybou.")
    send_notification()
    sys.exit()
except:
    # General exception if something wrong occurs
    logging.info("Neocekavana chyba.")
    logging.info("Program ukoncen s chybou.")
    send_notification()
    sys.exit()

# Deleting files in the archive folder
directory_check(archive_path,config.pocet_archiv)

logging.info("Program dobehl uspesne.")
