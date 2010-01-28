# coding: utf-8

import sys
import time
from plugins import Plugin
import settings

def get_plugins():
	return [AutoJoinPlugin()]

class AutoJoinPlugin(Plugin): 
	def __init__(self):
		pass
	
	def on_connected(self, bot):
		for channel in settings.channels:
			bot.join(channel)
