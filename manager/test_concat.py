from util import conf

from tasks.all import concat,filebot,assets_refresh
from celery import signature, chain, group, chord

to_concat_l = {"Insecure S02E08 Hella Perspective": 21,
"Insecure S02E05 Hella Shook":14,
"Insecure S02E07 Hella Disrespectful":14,
"Insecure S02E01 Hella Great": 16,
"Insecure S02E02 Hella Questions": 16,
"ATLANTA - S02 E02 - Sportin' Waves (720p - AMZN Web-DL)": 15,
"Insecure S02E03 Hella Open":15}
def test():
    for k,v in to_concat_l:
        file_ext = "mp4"
        if "Insecure" in k:
            file_ext = "mkv"
        routine = concat.s(num_range=range(v),file_name=k) | filebot.si(file_name=k,file_ext=file_ext) | assets_refresh.si()
        task = routine.delay()
        task.wait(timeout=None, interval=5)
