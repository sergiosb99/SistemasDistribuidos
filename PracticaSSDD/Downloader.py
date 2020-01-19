#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice, IceStorm
Ice.loadSlice('trawlnet.ice')
Ice.IPv6=0
Ice.IPv4=1
import TrawlNet
import hashlib

try:
    import youtube_dl
    import os
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

class DownloaderI(TrawlNet.Downloader):

    def __init__(self):
        self.publisher = None
    
    def addDownloadTask(self, link, current = None): 
        try:
            print("Download request: %s" %link)
            sys.stdout.flush()
            fileInfo = TrawlNet.FileInfo()
            fileInfo.name = download_mp3(link)
            fileInfo.hash = computeHash(fileInfo.name)
            self.publisher.newFile(fileInfo)
            return fileInfo
        except TrawlNet.DownloadError:
            print("Download failed")
            return 1

    def destroy(self, current):
        try:
            current.adapter.remove(current.id)
            print('DOWNLOADER DESTROYED', flush=True)
        except Exception as e:
            print(e, flush=True)

class DownloaderFactoryI(TrawlNet.DownloaderFactory):
    publisher = None
    def create(self, current): # EL ORCHESTRATOR INVOCA ESTE METODO, Y ESTA INTERFAZ LE DEVUELVE UN DOWNLOADER, AL CUAL EL ORCHESTRATOR DEBE MANDAR LA PETICION DE DESCARGA
        servant = DownloaderI()
        servant.publisher = self.publisher
        proxy = current.adapter.addWithUUID(servant)
        print('# New Downloader with proxy:', proxy, flush=True)

        return TrawlNet.DownloaderPrx.checkedCast(proxy)

class Downloader(Ice.Application):
    
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property", key,"not set")
            return None
        
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, args):
        
        self.broker = self.communicator() 
        self.sirvienteFactory = DownloaderFactoryI() #DownloaderI()
        self.adapter = self.broker.createObjectAdapter("DownloaderAdapter")
        self.proxy = self.adapter.addWithUUID(self.sirvienteFactory)
        
        print(self.proxy) 
        sys.stdout.flush()
        self.adapter.activate()

        ###### PUBLISHER UPDATE EVENT #######
        # Notifica de la descarga de archivos
        
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Invalid Proxy')
            return 2
        
        topic_name = "UpdateEvents"
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            print("No such topic found, creating")
            topic = topic_mgr.create(topic_name)

        publisher_event = topic.getPublisher()
        updateEvent = TrawlNet.UpdateEventPrx.uncheckedCast(publisher_event) 
        self.sirvienteFactory.publisher = updateEvent
				
        self.shutdownOnInterrupt()
        self.broker.waitForShutdown()
        
        return 0

downloader = Downloader()
sys.exit(downloader.main(sys.argv))






