import os
import subprocess
import datetime
import time
from watchdog.events import RegexMatchingEventHandler
import manager
import conf
from job_service import split_vid, convert_vid, waiting_for_vids, concat_vids, organize_vids

from log_it import get_logger

logger = get_logger(__name__)

class JobProducer(RegexMatchingEventHandler):
    VIDEO_REGEX = [r"^.*\.?(mkv|mp4|mpeg|m4v|flv|avi)$"]

    def __init__(self, convert_q, organize_q):
        super().__init__(self.VIDEO_REGEX)
        self.convert_q = convert_q
        self.organize_q = organize_q
        logger.info("New job producer made")
        

    def on_created(self, event):
        logger.info("Waiting for file to finish copying")
        file_size = -1
        while file_size != os.path.getsize(event.src_path):
            file_size = os.path.getsize(event.src_path)
            time.sleep(1)
        self.process(event)

    def process(self, event):
        logger.info("Processing new video file event")
        self.produce_jobs(event.src_path)

    
    def format_timedelta(self,time_delta):
        h_num = time_delta.seconds//3600
        m_num = (time_delta.seconds//60)%60
        s_num = time_delta.seconds - h_num*3600 - m_num*60
        hours = '0'+str(h_num) if len(str(h_num)) != 2  else str(h_num)
        minutes = '0'+str(m_num) if len(str(m_num)) != 2  else str(m_num)
        seconds = '0'+str(s_num) if len(str(s_num)) != 2  else str(s_num)
        return '%s:%s:%s' % (hours,minutes,seconds)

    def produce_jobs(self,file_name):
        intervals, chunk_prefix, chunk_suffix = self.get_intervals(file_name)
        split_job_id = self.create_split_job(file_name, chunk_prefix, chunk_suffix)
        self.create_convert_jobs(intervals, split_job_id)
        self.create_finishing_jobs(intervals, file_name)


    def create_finishing_jobs(self, intervals, file_name):
        output_file_name = conf.FILEBOT_DIR + "/"+ ".".join(file_name.split('/')[-1].split('.')[:-1]) + ".mp4"
        file_prefix = ".".join(file_name.split('/')[-1].split('.')[:-1])
        input_concat_vids = [interval["to_concat_name"] for interval in intervals]
        self.organize_q.enqueue(waiting_for_vids, description='waiting_for_vids-'+str(len(input_concat_vids)), args=(input_concat_vids,), job_timeout=9000)
        self.organize_q.enqueue(concat_vids, description='concat_vids-'+str(len(input_concat_vids)), args=(input_concat_vids, output_file_name, file_prefix,))
        self.organize_q.enqueue(organize_vids, description='organize_vids-'+output_file_name, args=(file_name, output_file_name,))


    def create_split_job(self,file_name, chunk_prefix, chunk_suffix):
        job = self.convert_q.enqueue(split_vid, description="split_vid-"+file_name ,args=(file_name, chunk_prefix, chunk_suffix,))
        return job.id


    def create_convert_jobs(self, intervals, split_job_id):
        for interval in intervals:
            self.convert_q.enqueue(convert_vid, description="convert_vid-"+interval["chunk_name"], depends_on=split_job_id, args=(interval["chunk_name"], interval["chunk_output"],), job_timeout=1200)


    def get_intervals(self,file_name):
        cmd_tmp = """ffmpeg -i "%s" 2>&1 | grep Duration | cut -d ' ' -f 4 | sed s/,//"""
        cmd = cmd_tmp % file_name
        logger.info("About to run cmd: %s" % cmd)
        output = subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT).decode().strip()
        logger.info("output of cmd : %s" % output)
        video_len = output.split('.')[0].split(':')
        if len(video_len) == 3:
            total_delta = datetime.timedelta(hours=int(video_len[0]), minutes=int(video_len[1]), seconds=int(video_len[2]))
        else:
            total_delta = datetime.timedelta(minutes=int(video_len[0]), seconds=int(video_len[1]))
        interval_list = list()
        file_prefix = '.'.join(file_name.split('.')[:-1])
        chunk_prefix = conf.CHUNKED_DIR +'/' +file_prefix.split('/')[-1]+'-'
        chunk_processed_prefix = conf.CONVERTING_DIR +'/' +file_prefix.split('/')[-1]+'-'
        to_concat_prefix = conf.TO_CONCAT_DIR +'/' + file_prefix.split('/')[-1]+'-'
        chunk_suffix = file_name.split('.')[-1]
        cursor = datetime.timedelta(minutes=0)
        interval_delta = datetime.timedelta(seconds=300)
        cursor += interval_delta
        counter = 0
        while cursor < total_delta:
            interval_dict = {}
            interval_dict["chunk_name"] = chunk_prefix + "{:0>2d}".format(counter) +"."+ chunk_suffix
            interval_dict["chunk_output"] = chunk_processed_prefix + "{:0>2d}".format(counter) +".mp4"
            interval_dict["to_concat_name"] =  to_concat_prefix + "{:0>2d}".format(counter) +".mp4"
            interval_list.append(interval_dict)
            cursor = cursor + interval_delta
            counter += 1

        interval_dict = {}
        interval_dict["chunk_name"] = chunk_prefix + "{:0>2d}".format(counter) +"."+ chunk_suffix
        interval_dict["chunk_output"] = chunk_processed_prefix + "{:0>2d}".format(counter) +".mp4"
        interval_dict["to_concat_name"] =  to_concat_prefix + "{:0>2d}".format(counter) +".mp4"
        interval_list.append(interval_dict)
        return interval_list, chunk_prefix, chunk_suffix




                










