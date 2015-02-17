import shlex
import subprocess
import datetime
import random
import glob
import json
from easyprocess import Proc


def kill_proc(proc, timeout):
  timeout["value"] = True
  proc.kill()

def run(cmd, timeout_sec):
  proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  timeout = {"value": False}
  timer = Timer(timeout_sec, kill_proc, [proc, timeout])
  timer.start()
  stdout, stderr = proc.communicate()
  timer.cancel()
  return proc.returncode, stdout.decode("utf-8"), stderr.decode("utf-8"), timeout["value"]

def load_users():
	json_data=open('users.json')	
	data = json.load(json_data)
	return data

def greet(user):
	#cmd=shlex.split("ping {0}".format(user['ip']))
	cmd=shlex.split("say \"{0} has entered the building\"".format(user['name']))	
	stdout=Proc(cmd).call(timeout=10).stdout

def log(message):
	print message
	pass	

def song_for_user(user):
	directory="themes/{0}".format(user['name'])
	onlyfiles=glob.glob("{0}/*.*".format(directory))
	if len(onlyfiles)==0:
		return False

	random_index=random.randint(0, len(onlyfiles) - 1)
	return onlyfiles[random_index]	

def play_song(user):	
	
	print "play song for {0}".format(user['name'])	
	file_to_play = song_for_user(user)
	if not file_to_play:
		return greet(user)

	print "playing {0}".format(file_to_play)	
	stdout=Proc(["afplay", file_to_play]).call(timeout=10).stdout	


def should_play_song(user, start_time):
	# If we haven't confirmed they aren't there, then don't play
	if not user['confirmed_not_there']:
		log("{0} was not confirmed to not be there".format(user['name']))
		return False

	# If we have confirmed they were previously not there and last_seen isn't set then play
	if not 'last_seen' in user:
		# Did we just restart the script?		
		five_mins_ago=datetime.datetime.now() - datetime.timedelta(minutes=5)
		if five_mins_ago > datetime.datetime.now():
			return True
		else:
			log("{0} was never seen but we just restarted the script".format(user['name']))
			return False

	# if last seen is set and it's older than 15 mins return true
	time_ago=15
	distant_time=datetime.datetime.now() - datetime.timedelta(minutes=time_ago)
	if user['last_seen'] < distant_time:
		log("{0} was last seen more than {1} mins ago".format(user['name'], time_ago))
		return True
	else:
		# otherwise dont play
		log("Dont play for {0} delta was lest than 1 min {1} - {2}".format(user['name'], user['last_seen'], distant_time))
		return False	


users = load_users()
start_time = datetime.datetime.now()

while 1:
	for user in users:

		if not 'confirmed_not_there' in user:
			user['confirmed_not_there'] = False

		try:
			cmd=shlex.split("ping {0}".format(user['ip']))
			# subprocess.check_output(cmd)
			stdout=Proc(cmd).call(timeout=1.6).stdout	    	

			if "bytes from" in stdout:						
				if should_play_song(user, start_time):
					play_song(user)							
				log("User: {0} is Reachable. {1}".format(user['name'], user['ip']))
				user['last_seen'] = datetime.datetime.now()
				user['confirmed_not_there'] = False
			else:
				user['confirmed_not_there'] = True
				last_seen = user['last_seen'] if 'last_seen' in user else "never"
				log("User: {0} is NotReachable. last seen: {1}".format(user['name'], last_seen))
		except subprocess.CalledProcessError,e:
		   print "ERROR {0}".format(e)
		else:
		   pass

