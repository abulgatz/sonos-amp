import os
import sys
import time
import re
import urllib, urllib2
import telnetlib
import soco
import Queue
import signal
from datetime import datetime
from Avr import Avr

rooms = []

rooms.append({'name': "Den", 'sonos_ip': "192.168.1.40", 'avr_ip': "192.168.1.30", 'avr_input': "SICD"})
rooms.append({'name': "MBR", 'sonos_ip': "192.168.1.41", 'avr_ip': "192.168.1.32", 'avr_input': "SIAUX1"})
# rooms.append({'name': "Patio", 'avr_ip': "192.168.1.30", 'sonos_ip': "192.168.1.", 'avr_input': "Z2CD"})
rooms.append({'name': "Patio", 'sonos_ip': "192.168.1.42"})
rooms.append({'name': "Breakfast L", 'sonos_ip': "192.168.1.43"})
rooms.append({'name': "Kitchen L", 'sonos_ip': "192.168.1.44"})
rooms.append({'name': "Kitchen Sub", 'sonos_ip': "192.168.1.45"})
rooms.append({'name': "Kitchen R", 'sonos_ip': "192.168.1.46"})
rooms.append({'name': "Breakfast R", 'sonos_ip': "192.168.1.47"})
rooms.append({'name': "Master Bath R", 'sonos_ip': "192.168.1.48"})
rooms.append({'name': "Master Bath L", 'sonos_ip': "192.168.1.49"})
rooms.append({'name': "Adam Bed", 'sonos_ip': "192.168.1.50"})
rooms.append({'name': "Adam Sink L", 'sonos_ip': "192.168.1.51"})
rooms.append({'name': "Adam Sink R", 'sonos_ip': "192.168.1.52"})
rooms.append({'name': "Theater", 'sonos_ip': "192.168.1.53", 'avr_ip': "192.168.1.31", 'avr_input': "SISAT/CBL"})

event_delay = 0.5
requested_subscription_time = 120


def subscribe(room):
	print u"{} *** Subscribing to {}".format(datetime.now(), room['name']).encode('utf-8')
	try:
		time.sleep(2)
		return room['sonos_device'].avTransport.subscribe(requested_timeout=requested_subscription_time, auto_renew=True)
	except Exception as e:
		print u"{} *** Subscribe failed to {}: {}".format(datetime.now(), room['name'], e).encode('utf-8')
		time.sleep(10)

def unsubscribe(room):
	print u"{} *** Unsubscribing from {}".format(datetime.now(), room['name']).encode('utf-8')
	try:
		room['subscription'].unsubscribe()
	except Exception as e:
		print u"{} *** Unsubscribe failed to {}: {}".format(datetime.now(), room['name'], e).encode('utf-8')

def stop_listener():
	try:
		soco.events.event_listener.stop()
	except Exception as e:
		print u"{} *** Stop event listern failed in: {}".format(datetime.now(), e).encode('utf-8')

def is_own_coordinator(room):
	try:
		if room['sonos_device'].group.coordinator == room['sonos_device']:
			return True
		else:
			return False
	except Exception as e:
		print u"{} *** Coordinator check failed in {}: {}".format(datetime.now(), room['name'], e).encode('utf-8')
		return False

def avr_set(room):
#	if room['avr_input'].startswith('Z2'):
		# do zone 2 stuff
#	else:
	if room['avr'].is_off():
		room['avr'].command(room['avr_input'])
		time.sleep(5)
		room['avr'].vol_ref()
		time.sleep(1)
	else:
		room['avr'].command(room['avr_input'])
		time.sleep(2)
		room['avr'].vol_ref()
		time.sleep(1)

def handle_sigterm(*args):
	global break_loop
	print u"SIGTERM caught. Exiting gracefully.".encode('utf-8')
	break_loop = True

def close_program():
	for room in rooms:
		room['subscription'].unsubscribe()
	soco.events.event_listener.stop()

break_loop = False

# Create avrs and sonos_devices from IP addresses, initialize other room vars
for room in rooms:
	room['avr'] = None
	if 'avr_ip' in room:
		room['avr'] = Avr(room['avr_ip'])
	room['sonos_device'] = soco.SoCo(room['sonos_ip'])
	room['subscription'] = None
	room['last_status'] = None
	room['last_coord_status'] = None

# Main loop
while True:
	
	# If any room is missing a subscription
	if any(not room['subscription'] or not room['subscription'].is_subscribed or room['subscription'].time_left <= 5 for room in rooms):
			print u"{} *** Missing subscription(s)".format(datetime.now()).encode('utf-8')
			
			# Check if there are any rooms with subscriptions
			if any(room['subscription'] for room in rooms):
				
				# If there are, kill all subscriptions
				for room in rooms:
					unsubscribe(room)
				
				# And stop the event listener
				stop_listener()

			# Now subscribe for each room
			for room in rooms:
				room['subscription'] = subscribe(room)
				print u"{} *** Subscribed to: {}".format(datetime.now(), room['name']).encode('utf-8')
	# End subscription block

	# For each room
	for room in rooms:

		status = None
		
		# Get latest events from queue
		try:
			event = room['subscription'].events.get(timeout=event_delay)
			status = event.variables.get('transport_state')

			# If invalid status
			if not status:
				print u"{} {} invalid status: {}".format(datetime.now(), room['name'], event.variables).encode('utf-8')

			# If status changed, print status
			if room['last_status'] != status:
				print u"{} {} status: {}".format(datetime.now(), room['name'], status).encode('utf-8')
		except Queue.Empty:
			pass
		except KeyboardInterrupt:
			handle_sigterm()

		# Is device a coordinator?
		if is_own_coordinator(room):
			# If player status has changed to playing, turn on AVR, set volume and input
			if room['last_status'] != 'PLAYING' and status == 'PLAYING' and 'avr_ip' in room:
				avr_set(room)
				print u"{} {} setting avr input to: {}".format(datetime.now(), room['name'], room['avr_input']).encode('utf-8')

			room['last_coord_status'] = None
		
		# Device is not coordinator
		else:
			# If not a coordinator, device status will always be "PLAYING", even if the coordinator is paused or stopped
			# so we need to rely on the coordinator's status instead
			
			# Get the coordinator device
			coord_device = room['sonos_device'].group.coordinator

			# Find its associated room (will return as list of 1 element)
			coord_rooms = [match for match in rooms if match['sonos_device'] == coord_device]
			
			# Extract coordinator room from list
			coord_room = coord_rooms[0]

			# If coordinator status changed, print status
			if room['last_coord_status'] != coord_room['last_status']:
				print u"{} {} coordinated by {} status: {}".format(datetime.now(), room['name'], coord_room['name'], coord_room['last_status']).encode('utf-8')
			
			# If coordinator status has changed to playing, turn on AVR, set volume and input
			if room['last_coord_status'] != 'PLAYING' and coord_room['last_status'] == 'PLAYING' and 'avr_ip' in room:
				avr_set(room)
				print u"{} {} coordinated by {} setting avr input to: {}".format(datetime.now(), room['name'], coord_room['name'], room['avr_input']).encode('utf-8')

			room['last_coord_status'] = coord_room['last_status']
		# End of if avr block

		if status:
			room['last_status'] = status
	# End for each room block


	if break_loop:
		close_program()
		break