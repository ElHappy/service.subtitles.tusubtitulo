# -*- coding: utf-8 -*-

# based on subtitulos.es subtitles
# developed by El_Happy for use TuSubtitulo (unofficially) and XBMC.org

import xbmc
import xbmcaddon
import re
import urllib
from operator import itemgetter
from utils import languages, alternatives
from bs4 import BeautifulSoup

__scriptid__ = xbmcaddon.Addon().getAddonInfo('id')
settings = xbmcaddon.Addon(id=__scriptid__)

main_url = "http://www.tusubtitulo.com/"

def log(module, msg):
  xbmc.log((u"### [%s] - %s" % (module,msg)).encode('utf-8'), level=xbmc.LOGDEBUG)

def search_tvshow(tvshow, season, episode, languages, filename):
  subs = list()
  temp_tvshow = []
  for level in range(5):
    searchstring, ttvshow, sseason, eepisode = getsearchstring(tvshow, season, episode, level)
    log("SEARCHSTRING", searchstring)
    if ttvshow not in temp_tvshow:
      url = main_url + searchstring.lower()
      subs.extend(getallsubsforurl(url, languages, None, ttvshow, sseason, eepisode, level))
      temp_tvshow.append(ttvshow)

  subs = clean_subtitles_list(subs)
  subs = order_subtitles_list(subs)
  return subs

def getsearchstring(tvshow, season, episode, level):

  # Clean tv show name
  if level == 1 and re.search(r'\([^)][a-zA-Z]*\)', tvshow):
    # Series name like "Shameless (US)" -> "Shameless US"
    tvshow = tvshow.replace('(', '').replace(')', '')

  if level == 2 and re.search(r'\([^)][0-9]*\)', tvshow):
    # Series name like "Scandal (2012)" -> "Scandal"
    tvshow = re.sub(r'\s\([^)]*\)', '', tvshow)

  if level == 3 and re.search(r'\([^)]*\)', tvshow):
    # Series name like "Shameless (*)" -> "Shameless"
    tvshow = re.sub(r'\s\([^)]*\)', '', tvshow)

  if level == 4 and tvshow in alternatives:
    # Clean name like "Serie (*)" -> "Serie"
    tvshow = re.sub(r'\s\([^)]*\)', '', tvshow)
    # Search alternative name "Serie" -> "Serie 2014"
    tvshow = alternatives[tvshow]

  # Build search string
  searchstring = 'serie/' + tvshow + '/' + season + '/' + episode + '/*'

  # Replace spaces with dashes
  searchstring = re.sub(r'\s', '-', searchstring)

  # Replace simple comma
  searchstring = re.sub(r'\'', '%27', searchstring)

  return searchstring, tvshow, season, episode

def getallsubsforurl(url, langs, file_original_path, tvshow, season, episode, level):

  subtitles_list = []

  content = geturl(url)
  soup = BeautifulSoup(content, 'html.parser')

  # Search list of subtitles
  for f in soup.find_all(text=re.compile(u'Versión')):
    filename = f.strip()
    if filename != None:
      filename = re.sub(u'Versión', '', filename.strip())
      filename = re.sub(r' ', '.', filename)
      filename = re.sub(r'\s', '.', tvshow) + "." + season + "x" + episode + filename
      filename = re.sub(r'..0.00.megabytes', '', filename)
      filename = re.sub(r'.0.00.megabytes', '', filename)
      filename = re.sub(r', 0.00 megabytes', '', filename)
      server = filename
      backup = filename
      log("FILENAME", filename)

      # Search content of every subtitle
      for l in f.parent.parent.parent.parent.find_all('li'):
        
        # Take language of subtitle
        if l.find('b') != None:
          lang = re.sub(u'ñ', 'n', l.find('b').text.strip())
          lang = re.sub(u'á', 'a', lang)
          lang = re.sub(u'é', 'e', lang)
          lang = re.sub(u'à', 'a', lang)
          log("LANG", lang)

          if lang in languages:
            languageshort = languages[lang][1]
            languagelong = languages[lang][0]
            filename = filename + ".(%s)" % languages[lang][2]
            server = filename
            order = 1 + languages[lang][3]
          else:
            lang = "Unknown"
            languageshort = languages[lang][1]
            languagelong = languages[lang][0]
            filename = filename + ".(%s)" % languages[lang][2]
            server = filename
            order = 1 + languages[lang][3]
          continue

        # Take state of subtitle
        if l.text.strip() == 'Completado':
          state = l.text.strip()
          log("STATE", state)
          continue

        # Take link of subtitle
        if l.find('a') != None:
          link = "http://www.tusubtitulo.com/" + l.find('a').get('href')
          log("LINK", link)

        # Just add complete subtitles
        if lang != None and state != None and link != None and languageshort in langs:
          subtitles_list.append({'no_files': 1, 'filename': filename, 'server': server, 'sync': False, 'language_flag': languageshort + '.gif', 'language_name': languagelong, 'hearing_imp': False, 'link': link, 'lang': languageshort, 'order': order})
          lang = None
          state = None
          link = None
          filename = backup
          server = backup

  return subtitles_list

def geturl(url):
  class AppURLopener(urllib.FancyURLopener):
    version = "User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    def __init__(self, *args):
      urllib.FancyURLopener.__init__(self, *args)
    def add_referrer(self, url=None):
      if url:
        urllib._urlopener.addheader('Referer', url)

  if settings.getSetting('PROXY') == 'true':
    log("PROXY", "Proxy enabled")
    proxy = {settings.getSetting('PROXY_PROTOCOL') : settings.getSetting('PROXY_PROTOCOL') + '://' + settings.getSetting('PROXY_HOST') + ':' + settings.getSetting('PROXY_PORT')}
    urllib._urlopener = AppURLopener(proxy)
  else:
    log("PROXY", "Proxy disabled")
    urllib._urlopener = AppURLopener()
  urllib._urlopener.add_referrer("http://www.tusubtitulo.com/")
  try:
    response = urllib._urlopener.open(url)
    content = response.read()
  except:
    content = None
  return content

def clean_subtitles_list(subtitles_list):
  seen = set()
  subs = []
  for sub in subtitles_list:
    filename = sub['link']
    if filename not in seen:
      subs.append(sub)
      seen.add(filename)
  return subs

def order_subtitles_list(subtitles_list):
  return sorted(subtitles_list, key=itemgetter('order')) 
