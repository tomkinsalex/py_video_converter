import json
import urllib.request
from util import conf
from util.log_it import get_logger

logger = get_logger(__name__)

def is_new_content(path):
    body = { 'path': path }
    return bool(send_request(conf.API_IS_NEW_URL, body))


def post_new_video(path):
    body = { 'path': path }
    return send_request(conf.API_POST_URL, body)


def send_request(url, body):
    logger.info("Sending request to url: %s" % url)
    logger.info("Body: %s" % str(body))
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(body)
    jsondataasbytes = jsondata.encode('utf-8')
    req.add_header('Content-Length', len(jsondataasbytes))
    resp = urllib.request.urlopen(req, jsondataasbytes).read().decode("utf-8")
    logger.info('Response: %s' % resp)
    return resp