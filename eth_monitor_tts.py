#!/usr/bin/env python3

from time import sleep
from os import devnull, path
from datetime import datetime
import subprocess
import sys
from gtts import gTTS
from playsound import playsound


sound_notifications = {
	"LU.mp3": "LAN up",
	"LD.mp3": "LAN down",
	"WU.mp3": "Internet up",
	"WD.mp3": "Internet down",
	"end.mp3": "Leaving now"
}


def create_sounds(file_text):
	for filename, text in file_text.items():
		if not path.isfile(filename):
			tts = gTTS(text=text, lang='en')
			tts.save(filename)
			print(f"saved {filename}")


def play_sound(filename):
	playsound(filename, True)


def notify_lan(is_up):
	if is_up:
		play_sound("LU.mp3")
	else:
		play_sound("LD.mp3")


def notify_wan(is_up):
	if is_up:
		play_sound("WU.mp3")
	else:
		play_sound("WD.mp3")


def get_default_gw():
	return subprocess.check_output("route -n -4 | awk 'FNR == 3 {print $2}'", shell=True).decode("utf-8")[:-1]


FNULL = open(devnull, 'w')
IP_WAN = ("185.2.86.72", "212.55.154.194", "1.1.1.1", "8.8.8.8")
IP_DGW = get_default_gw()


def is_online(ip):
	return subprocess.call(f"ping -c 1 -W 1 {ip}", shell=True, stderr=FNULL, stdout=FNULL) == 0


def check_connectivity(ip_list, retry=3):
	if isinstance(ip_list, str):
		ip_list = (ip_list, )

	attempt = 0
	while attempt < retry:
		ip = ip_list[attempt % len(ip_list)]
		if is_online(ip):
			return True
		attempt += 1

	return False


def monitor_eth(loop_sec=12*3600, sleep_sec=4.0):
	lan_last_status = io_lan = not check_connectivity(IP_DGW)
	wan_last_status = io_wan = not check_connectivity(IP_WAN)
	eth_changes = False
	print(f"dgw={IP_DGW}")

	while loop_sec > 0:
		loop_sec -= sleep_sec

		io_lan = check_connectivity(IP_DGW)
		if lan_last_status != io_lan:
			lan_last_status = io_lan
			eth_changes = True
			notify_lan(io_lan)

		if io_lan:
			io_wan = check_connectivity(IP_WAN)
			if wan_last_status != io_wan:
				wan_last_status = io_wan
				eth_changes = True
				notify_wan(io_wan)
		else:
			wan_last_status = False

		if eth_changes:
			eth_changes = False
			print(f"{datetime.now()} | LanUp: {str(io_lan):5} | WanUp: {str(io_wan):5} |")
		else:
			sleep(sleep_sec)

	play_sound("end.mp3")


def get_duration():
	return int(sys.argv[1]) if len(sys.argv) == 2 else 4*3600


if __name__ == "__main__":
	create_sounds(sound_notifications)
	monitor_eth(loop_sec=get_duration())
