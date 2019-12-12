#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice, IceStorm
Ice.loadSlice('trawlnet.ice')
import TrawlNet
import hashlib

####################### CODIGO CAMPUS #######################

try:
    import youtube_dl
    import os # Añadido al material del campus, si no, no funciona.
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
    options['progress_hooks'] = [progress_hook]
    options['outtmpl'] = os.path.join(destination, '%(title)s.%(ext)s')
    with youtube_dl.YoutubeDL(options) as youtube:
        youtube.download([url])
    filename = task_status['filename']
    # BUG: filename extension is wrong, it must be mp3
    filename = filename[:filename.rindex('.') + 1]
    return filename + options['postprocessors'][0]['preferredcodec']

def computeHash(filename):
    '''SHA256 hash of a file'''
    fileHash = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            fileHash.update(chunk)
        return fileHash.hexdigest()

#############################################################

# Sirviente
class DownloaderI(TrawlNet.Downloader):

    def __init__(self):
        self.publisher = None
    
    def addDownloadTask(self, link, current = None): ## TRY EXCEPT
        try:
            print("Peticion de descarga: %s" %link)
            sys.stdout.flush()
            fileInfo = TrawlNet.FileInfo()
            fileInfo.name = download_mp3(link)
            fileInfo.hash = computeHash(fileInfo.name)
            self.publisher.newFile(fileInfo)
            return fileInfo
        except TrawlNet.DownloadError:
            print("Error en la descarga")
            return 1

# Servidor
class Downloader(Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property", key,"not set")
            return None
        
        print("Using IceStorm in: '%s'" % key) ### ESTO HABRÁ QUE QUITARLO POR EL SCRIPT!!!!!
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, args):
        self.broker = self.communicator() 
        self.sirviente = DownloaderI()
        self.adapter = self.broker.createObjectAdapter("DownloaderAdapter")
        self.proxy = self.adapter.addWithUUID(self.sirviente)
        
        # Imprimimos el proxy del downloader, lo necesita el orchestrator por parametros.        
        print(self.proxy) 
        sys.stdout.flush()
        self.adapter.activate()
        
        ## CÓDIGO PUBLISHER
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Proxy invalido')
            return 2
        
        topic_name = "UpdateEvents"
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            print("No such topic found, creating")
            topic = topic_mgr.create(topic_name)

        publisher_event = topic.getPublisher() # Se obtiene un publicador
        updateEvent = TrawlNet.UpdateEventPrx.uncheckedCast(publisher_event) 
        self.sirviente.publisher = updateEvent
        # El publisher de DownloaderI sera updateEvent, ya que luego invoca al método newFile
				
        self.shutdownOnInterrupt()
        self.broker.waitForShutdown()
        
        return 0

downloader = Downloader()
sys.exit(downloader.main(sys.argv))






