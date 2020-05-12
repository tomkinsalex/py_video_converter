from dotenv import load_dotenv
import os
from sys import platform

is_linux = platform == 'linux'

load_dotenv()
ROOT_DIR= os.getenv("ROOT_DIR") if is_linux else os.getenv("MAC_ROOT_DIR")
global FINAL_DIR
FINAL_DIR= '%s/home-caster-videos' % ROOT_DIR
global ASSETS_DIR
ASSETS_DIR='%s/home-caster-assets' % ROOT_DIR
global ASSET_TMP_DIR
ASSET_TMP_DIR='%s/home-caster-tmp' % ROOT_DIR
global TO_CONCAT_DIR
TO_CONCAT_DIR='%s/to_concat' % ROOT_DIR
global CHUNKED_DIR
CHUNKED_DIR='%s/chunked' % ROOT_DIR
global FILEBOT_DIR
FILEBOT_DIR='%s/for_filebot' % ROOT_DIR
global FILEBOT_LOG_FILE
FILEBOT_LOG_FILE='%s/logs/amc.log' % ROOT_DIR
global FILEBOT_PROCESSED_LIST
FILEBOT_PROCESSED_LIST='%s/logs/processed.txt' % ROOT_DIR
global DROP_ZONE_DIR
DROP_ZONE_DIR=os.getenv("DROP_ZONE_DIR") if is_linux else os.getenv("MAC_DROP_ZONE_DIR")
global CONVERTING_DIR
CONVERTING_DIR='%s/converting' % ROOT_DIR
global REDIS_HOST
REDIS_HOST=os.getenv("REDIS_HOST") if is_linux else os.getenv("MAC_REDIS_HOST")
global PROCESSED_PICS_LOG
PROCESSED_PICS_LOG='%s/logs/processed_pics.txt' % ROOT_DIR
global Q_ALL_HOSTS
Q_ALL_HOSTS="q_all_hosts"
global Q_PIS
Q_PIS="q_pis"
global RESULT_CSV_FILE
RESULT_CSV_FILE='%s/logs/results.csv' % ROOT_DIR
global STATS
STATS=os.getenv("STATS")
