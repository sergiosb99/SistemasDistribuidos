#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice, IceStorm
Ice.loadSlice('trawlnet.ice')
import TrawlNet

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

#############################################################

# Sirviente
class DownloaderI(TrawlNet.Downloader):
    def addDownloadTask(self, link, current = None):
        print("Peticion de descarga: %s" %link)
        sys.stdout.flush()
        fileInfo = TrawlNet.FileInfo()
        fileInfo.name = download_mp3(link)
        #file.hash = metodo que nos tienen que pasar
        return fileInfo

# Servidor
class Downloader(Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property", key,"not set")
            return None
        
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, args):
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

        self.publisher = topic.getPublisher()
        self.updateEvent = TrawlNet.UpdateEventPrx.uncheckedCast(self.publisher) ## DUDAS
    
        #AQUI DEBERÍA DE IR EL CODIGO LLAMANDO A LA FUNCION DE LA INTERFAZ CREO     
        self.updateEvent.newFile(hay que pasarle un fileInfo)

        #NO SE SI ESTO SIGUE ASÍ
        self.broker = self.communicator() 
        self.sirviente = DownloaderI()

        self.adapter = self.broker.createObjectAdapter("DownloaderAdapter")
        self.proxy = self.adapter.addWithUUID(self.sirviente)
        #self.proxy = self.adapter.add(self.sirviente, self.broker.stringToIdentity("downloader1"))
        print(self.proxy)
        sys.stdout.flush()
        self.adapter.activate()
				
        self.shutdownOnInterrupt()
        self.broker.waitForShutdown()
        
        return 0

downloader = Downloader()
sys.exit(downloader.main(sys.argv))






