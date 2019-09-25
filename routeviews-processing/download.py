import os
import requests
from BeautifulSoup import BeautifulSoup
import time
from urlparse import urlparse
from threading import Thread
import httplib
from Queue import Queue
import uuid
import json
import wget
import sys

BASE_URL = "archive.routeviews.org"
DEFAULT  = "" # default is route-views1
collector = [
DEFAULT, 
# "route-views3",
# "route-views4",
# "route-views6",
# "route-views.amsix",
# "route-views.chicago",
# "route-views.chile",
# "route-views.eqix",
# "route-views.flix",
# "route-views.isc",
# "route-views.jinx",
# "route-views.kixp",
# "route-views.linx",
# "route-views.mwix",
# "route-views.napafrica",
# "route-views.nwax",
# "route-views.perth",
# "route-views.saopaulo",
# "route-views.sfmix",
# "route-views.sg",
# "route-views.soxrs",
# "route-views.sydney",
# "route-views.telxatl",
# "route-views.wide",
# "route-views2.saopaulo",
]



def gen_input(month, input_file):
	wget_input = []
	for ct in collector:
		src = os.path.join(BASE_URL, ct, "bgpdata", month, "UPDATES")
		src_url = "http://%s" % src
		dst_dir = src

		if not os.path.exists(dst_dir):
			os.makedirs(dst_dir)

		r = requests.get(src_url)
		soup = BeautifulSoup(r.text)
		for tag in soup.findAll('a', href=True):
			fn = tag['href']
			if not fn.endswith(".bz2"):
				continue 
			file_src = "%s/%s" % (src_url, fn)
			file_dst = "%s/%s" % (dst_dir, fn)
			print file_src, file_dst
			wget_input.append("%s %s\n" % (file_src, file_dst))

	open(input_file, "w").writelines(wget_input)

def downloader(src, dst):
	if os.path.exists(dst):
		os.remove(dst)
	wget.download(src, dst)

class Worker():
    """
    A queue-based multiple threading framework for sending
    parallel requests
    """

    def __init__(self, logger, work_no, func):
        self.logger = logger
        self.work_no = work_no
        self.func = func
        self.q = Queue(10000)
        self.task_no = 0


    def clear_queue(self):
        with self.q.mutex:
            self.q.queue.clear()

    def run_task(self, task):
        while True:
            work_id, para = self.q.get()
            res = task(para)
            self.q.task_done()

    def init(self):
        for i in range(self.work_no):
            t = Thread(target=self.run_task, args=(self.task,))
            t.daemon = True
            t.start()

    def add_tasks(self, para_list):
        self.task_no = len(para_list)
        try:
            for i in xrange(self.task_no):
                para = para_list[i]
                work_id = i
                self.q.put((work_id, para))
            self.q.join()
        except KeyboardInterrupt:
            sys.exit(1)

    def task(self, para):
        res = self.func(*para)
        open(self.logger, "a").write("%s %s\n" % (para[0], para[1]))
        return res
 

if __name__ == '__main__':
    month = sys.argv[1]
    input_file = sys.argv[2]
    th_no = int(sys.argv[3])
    logger_file = sys.argv[4]
    
    gen_input(month, input_file)
    inputs = [tuple(v.strip("\n").split(" ")) for v in open(input_file).readlines()]
    wd = Worker(logger_file, th_no, downloader)
    wd.init()
    wd.add_tasks(inputs)
