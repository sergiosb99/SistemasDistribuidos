#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

####################### CODIGO CAMPUS #######################

try:
	import youtube_dl
except ImportError:
	print('ERROR: do you have installed youtube-dl library?')
	sys.exit(1)

class NullLogger:
	def debug(self, msg):
		pass

	def warning(self, msg):
		pass

	def error(self, msg):
		pass

_YOUTUBEDL_OPTS_ = {
	'format': 'bestaudio/best',
	'postprocessors': [{
		'key': 'FFmpegExtractAudio',
		'preferredcodec': 'mp3',
		'preferredquality': '192',
	}],
	'logger': NullLogger()
}

def download_mp3(url, destination='./'):
	'''
	Synchronous download from YouTube
	'''

	options = {}
	task_status = {}
	def progress_hook(status):
		task_status.update(status)
	options.update(_YOUTUBEDL_OPTS_)
	options['progress_hooks'] = [progress_hook
	options['outtmpl'] = os.path.join(destination, '%(title)s.%(ext)s')
	with youtube_dl.YoutubeDL(options) as youtube:
			youtube.download([url])
	filename = task_status['filename']
	# BUG: filename extension is wrong, it must be mp3
	filename = filename[:filename.rindex('.') + 1]
	return filename + options['postprocessors'][0]['preferredcodec']

#############################################################

# Sirviente
class DownloaderI (TrawlNet.Downloader):
    def addDownloadTask(self, link, current = None):
        #print("Petición de descarga: %s" %link, flush=True)
        print("Peticion de descarga: %s" %link)
        sys.stdout.flush()
        output_file = download_mp3(link) 
        print("Archivo descargado: %s" %output_file)
        return output_file

# Servidor
class Downloader (Ice.Application):
    def run(self, args):
        broker = self.communicator() 
        sirviente = DownloaderI() # Se crea una instancia del sirviente
		# Se crea el adaptador de objetos
        adapter = broker.createObjectAdapter("DownloaderAdapter") # El adaptador requiere un endpoint, un host y un puerto, están en server.config
        proxy = adapter.addWithUUID(sirviente) # UUID crea una secuencia unica
		#print(str(proxy), flush = True)
        print(proxy) # Esto seguramente habrá que borrarlo más adelante.
        sys.stdout.flush()

        adapter.activate() # El adaptador se ejecuta en otro hilo
		
		#A partir de este momento el servidor escucha peticiones
		
        self.shutdownOnInterrupt() # Ctrl + C, fin de la aplicación (SIGQUIT)
        broker.waitForShutdown() # Bloquea el hilo principal hasta que el comunicador sea terminado

        return 0
#main 
downloader = Downloader()
sys.exit(downloader.main(sys.argv))
		





