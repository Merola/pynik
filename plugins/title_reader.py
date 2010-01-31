# coding: utf-8

import sys
import re
import time
import utility
from plugins import Plugin
from commands import Command
import command_catcher

class URL():
	url = ''
	title = ''
	timestamp = ''
	nick = ''
	def is_match(self, searchword):
		if self.url and re.search(searchword, self.url, re.IGNORECASE):
			return True
		if self.title and re.search(searchword, self.title, re.IGNORECASE):
			return True
		if self.nick and re.search(searchword, self.nick, re.IGNORECASE):
			return True
		return False


def get_title(url):
	import urllib
	if not re.search('https?', url):
		url = 'http://' + url

	response = utility.read_url(url)
	data = response["data"]

	data = data.replace("\r", "").replace("\n", "")

	m = re.search('<title[^>]*>\s*(.+?)\s*<\/title>', data, re.IGNORECASE|re.MULTILINE)

	if m:
		title = m.group(1)
		title = re.sub('\s+', ' ', title)
		return utility.unescape(re.sub('<.+?>', '', title))
	else:
		return None


class TitleReaderPlugin(Command):
	hooks = ['on_privmsg']
	last_urls = {}
	url_lists = {}
	url_masks = {}


	def get_url_list(self, channel):
		if channel not in self.url_lists:
			self.url_lists[channel] = []
		
		return self.url_lists[channel]


	def __init__(self):
		pass


	def on_privmsg(self, bot, source, target, message):
		m = re.search('((https?:\/\/|www.)\S+)', message, re.IGNORECASE)

		if m:
			url = m.group(1)
			
			url_obj = URL()
			url_obj.url = m.group(1)
			url_obj.nick = source
			url_obj.timestamp = time.localtime()
			url_obj.title = get_title(url)
			
			self.last_urls[target] = url_obj
			self.save_last_url(target)
			
			if target in ['#c++.se', '#d1d', '#lithen', "#d2006"]:
				bot.tell(target, self.clean(url_obj.url, url_obj.title))


	def save_last_url(self, target):
		self.get_url_list(target).append(self.last_urls[target])
		self.save_urls()


	def trig_urlsearch(self, bot, source, target, trigger, argument):
		resultlist = []
		match = False

		if len(argument) > 0:
			searchlist = argument.split(' ')

			for url_obj in self.get_url_list(target):
				match = True
				for word in searchlist:
					if not url_obj.is_match(word):
						match = False
						break
				if match:
					resultlist.append(url_obj)

			if len(resultlist) > 0:
				if resultlist[-1].title:
					title = resultlist[-1].title
				else:
					title = 'N/A'
				return 'Match 1 of ' + str(len(resultlist)) + ': ' + resultlist[-1].url + ' - ' + title
			else:
				return 'No match found.'
		else:
			return 'Usage: .urlsearch <search string>'


	def trig_title(self, bot, source, target, trigger, argument):
		url = argument.strip()
		
		if not url:
			if target not in self.last_urls.keys():
				return 'I haven\'t seen any urls here yet.'
			
			url = self.last_urls[target].url
			title = self.last_urls[target].title
			
		else:
			title = get_title(argument)
		
		if not title:
			return 'I can\'t find a title for ' + url
		else:
			return self.clean(url, title)


	def save_urls(self):
		utility.save_data("urls", self.url_lists)


	def load_urls(self):
		self.url_lists = utility.load_data("urls", {})


	def on_load(self):
		self.load_urls()
		self.mask_load()


	def save(self):
		pass


	def on_modified_options(self):
		self.save()


	def clean(self, url, title):
		sitematch = re.match(r'(?:http://|https://|)*(?:www\.)*(.+?)(?:\/.*|$)', url)

		if sitematch != None and sitematch.lastindex >= 1:
			site = sitematch.group(1)
		else:
			return(title)

		if site in self.url_masks.keys():
			result = re.match(self.url_masks[site], title)

			if result != None and result.lastindex >= 1: # we need at least one group
				return result.group(1)
			else:
				return title + " (full title)"

		else:
			# try partial matches. slow as shit, but whaddayagonnado.
			for eSite, eMask in self.url_masks.items():
				match = url.find(eSite)
				if (match != -1):
					return re.search(eMask, title).group(1)
  		return(title)


	def mask_load(self):
		self.url_masks = utility.load_data("urlmasks", {})


	def mask_save(self):
		utility.save_data("urlmasks", self.url_masks)


	def trig_titlemask(self, bot, source, target, trigger, argument):
		sArg = argument.strip()

		m = re.match(r'([^ ]+) *(.*)$', sArg)
		if not m:
			return 'usage: .titlemask <host> <regex> | regex can only have one capturing group'

		site = m.group(1)
		mask = m.group(2)

		if (mask.strip() == ''):
			if site in self.url_masks:
				return 'mask for ' + site + ' is ' + self.url_masks[site]
			else:
				return site + ' has no stored title mask.'
		try:
			compiledMask = re.compile(mask)
		except re.error:
		    return 'invalid regex for ' + site

		if compiledMask.groups < 1:
			return 'Needs exactly one capturing group.'

		if compiledMask.groups > 1:
			return 'Too many capturing groups. Use (?:pattern).'

		site = 	re.match(r'(?:http://|https://|)*(?:www\.)*(.+?)(?:\/.*|$)', site).group(1)
		self.url_masks[site] = mask
		self.mask_save()
		return 'mask '+ mask + ' saved for ' + site


	def trig_reloadtitlemasks(self, bot, source, target, trigger, argument):
		self.mask_load()
		return 'reloaded.'


	def trig_deltitlemask(self, bot, source, target, trigger, argument):
		site = argument.strip()
		if site == '':
			return "You forgot to specify a site. Silly hoo-man."
		if site in self.url_masks:
			del self.url_masks[site]
			self.mask_save()
			return 'mask cleared for ' + site
		else:
			return site + ' not found in title mask database.'

