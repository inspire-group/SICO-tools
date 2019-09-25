import sys
import os
import os
import requests
import time
from urlparse import urlparse
from threading import Thread
import httplib
from Queue import Queue
import uuid
import json
import md5

BASE_DIR = "archive.routeviews.org"
DEFAULT = ""

def gen_input(collector, month):
	path = os.path.join(BASE_DIR, collector, "bgpdata", month, "UPDATES")
	if collector == "route-views1": # specific case
		path = os.path.join(BASE_DIR, DEFAULT, "bgpdata", month, "UPDATES")
	tmp = [f for f in os.listdir(path) if f.endswith(".bz2") and not f.startswith(".")]
	fs = [os.path.join(path, f) + "\n" for f in tmp]
	fs.sort()
	fout = "%s_fs_input.csv" % collector 
	open(fout, "w").writelines(fs)
	return fout

class Worker():
	"""
	A queue-based multiple threading framework for sending
	parallel requests
	"""

	def __init__(self, logger, out_dir, work_no, func):
		self.logger = logger
		self.out_dir = out_dir
		self.work_no = work_no
		self.func = func
		self.q = Queue(10000)
		self.task_no = 0
		self.output = {}


	def clear_queue(self):
		with self.q.mutex:
			self.q.queue.clear()

	def run_task(self, task):
		while True:
			work_id, para = self.q.get()
			res = task(para)
			for k in res: self.output[k] = None
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
			
			fout = "%s/%s.csv" % (self.out_dir, para[1])
			print fout, len(self.output)
			if len(self.output) > 0:
				open(fout, "w").writelines(self.output.keys())

		except KeyboardInterrupt:
			sys.exit(1)

	def task(self, para):
		"""
		Customized your task here
		"""
		res = self.func(*para)
		open(self.logger, "a").write("%s\n" % para[0])
		return res



def get_asn_cmt(fin, collector):
	cmd = "bgpdump -ml %s" % fin
	buf = {}
	cnt = 0
	for e in os.popen(cmd):
		cnt += 1
		_e = e.split("|")
		if _e[2] != "A" or (not _e[-5] and not _e[-4]):
			continue
		cmt = _e[-5]
		cmt_large = _e[-4]
		as_path = _e[6]
		_str = "%s#%s#%s\n" % (as_path, cmt, cmt_large)
		buf[_str] = None
	return buf



if __name__ == '__main__':
	collector = sys.argv[1]
	month = sys.argv[2]
	th_no = int(sys.argv[3])
	out_dir = sys.argv[4]
	logger_file = sys.argv[5]
	
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	fout = gen_input(collector, month)
	inputs = [(v.strip("\n"), collector) for v in open(fout).readlines()]
	wd = Worker(logger_file, out_dir, th_no, get_asn_cmt)
	wd.init()
	wd.add_tasks(inputs)
