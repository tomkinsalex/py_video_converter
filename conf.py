from dotenv import load_dotenv
import os

def init():
    load_dotenv()
    global REDIS_PORT
    REDIS_PORT=6379
    ROOT_DIR= os.getenv("ROOT_DIR")
    global FINAL_DIR
    FINAL_DIR=ROOT_DIR +'/home-caster-videos'
    global ASSETS_DIR
    ASSETS_DIR=ROOT_DIR +'/home-caster-assets'
    global ASSET_TMP_DIR
    ASSET_TMP_DIR=ROOT_DIR +'/home-caster-tmp'
    global TO_CONCAT_DIR
    TO_CONCAT_DIR=ROOT_DIR +'/to_concat'
    global CHUNKED_DIR
    CHUNKED_DIR=ROOT_DIR +'/chunked'
    global FILEBOT_DIR
    FILEBOT_DIR=ROOT_DIR +'/for_filebot'
    global FILEBOT_LOG_FILE
    FILEBOT_LOG_FILE=ROOT_DIR +'/logs/amc.log'
    global FILEBOT_PROCESSED_LIST
    FILEBOT_PROCESSED_LIST=ROOT_DIR +'/logs/processed.txt'
    global DROP_ZONE_DIR
    DROP_ZONE_DIR=os.getenv("DROP_ZONE_DIR")
    global LOG_DIR
    LOG_DIR=os.getenv("LOG_DIR")
    global CONVERTING_DIR
    CONVERTING_DIR=ROOT_DIR+'/converting'