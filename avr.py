import socket
import string
from time import sleep
import re

LIMIT=135

class Avr:
	def __init__(self, addr, port = 23):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((addr, port))
		self.buffer = ''

	def close(self):
		self.sock.close()

	def command(self, message):
		self.sock.send(message + '\r')

	def response_recursive(self, buffer=''):
		data = self.sock.recv(LIMIT)
		if data.endswith('\r'):
			return data
		else:
			return buffer + self.response_recursive(data)

	def response(self):
		return filter(None, string.split(self.response_recursive(), '\r'))

#	def response(self):
#		if len(self.buf) < 2:
#			data = self.sock.recv(LIMIT)
#			n = string.split(data, '\r')
#			if len(self.buf) == 1:
#				n[0] = self.buf[0] + n[0]
#			self.buf = n
#		return self.buf.pop(0).strip()

#	def response_contains(self, function_to_run, num_times_run_function, value_to_check):
#		responses = []
#		for i in xrange(num_times_run_function):
#			responses.append(function_to_run())
#		
#			return True
#		else:
#			return False

	# *** Main zone power *********
	def power_on(self):
		self.command('PWON')

	def power_off(self):
		self.command('PWSTANDBY')

	def power_query(self):
		self.command('PW?')
		return self.response()

	def is_off(self):
		responses = self.power_query()
		if any(response == 'PWSTANDBY' for response in responses):
			return True
		return False

	# *** Zone 2 power *********
	def z2_power_on(self):
		self.command('Z2ON')

	def z2_power_on(self):
		self.command('')

	def z2_power_query(self):
		self.command('Z2?')
		return self.response()

	def z2_is_off(self):
		response = self.z2_power_query(self)
		if any(response == '' for response in responses):
			return True

	# *** Main zone volume & mute *********
	def vol_up(self):
		self.command('MVUP')

	def vol_down(self):
		self.command('MVDOWN')

	def vol_ref(self):
		self.command('MV80')

	def vol_query(self):
		self.command('MV?')
		return self.response()

	def mute(self):
		self.command('MUON');

	def unmute(self):
		self.command('MUOFF');

	def is_muted(self):
		self.command('MU?')
		return self.response() != "MUOFF"

	# *** Zone 2 volume & mute *********
	def z2_vol_ref(self):
		self.command('Z280')

	# *** Main zone input *********
	def select_dvr(self):
		self.command('SIDVR')

	def select_rhapsody(self):
		self.command('SIRHAPSODY')

	def select_hdp(self):
		self.command('SIHDP')

	def select_server(self):
		self.command('SIHDP')

	def select_cd(self):
		self.command('SICD')

	def select_aux1(self):
		self.command('SIAUX1')

	def source(self):
		self.command('SI?')
		return self.response()

	# *** Zone 2 input *********
	def z2_select_cd(self):
		self.command('Z2CD')

	# *** net screen ***
#	def onscreen_display(self):
#		self.command('NSE')
#		ret = []
#		for line in range(9):
#			n = self.response()
#			n = n[4:-1]
#			if line != 0 and line != 8:
#				# tag = n[0]
#				n = n[1:-1]
#			ret.append( n )
#		return string.join(ret, '\n')

	def osd(self):
		self.command('NSE')
		ret = []
		while (len(ret) < 9):
			ret.extend(self.response())
		return ret

	def print_utf8_list(self, my_list):
		for item in my_list:
			print u"{}".format(item).encode('UTF-8')



