#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
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
        return download_mp3(link) 

# Servidor
class Downloader(Ice.Application):
    def run(self, args):
        broker = self.communicator() 
        sirviente = DownloaderI()

        adapter = broker.createObjectAdapter("DownloaderAdapter")
        #proxy = adapter.addWithUUID(sirviente)
        proxy = adapter.add(sirviente, broker.stringToIdentity("downloader1"))
        print(proxy)
        sys.stdout.flush()
        adapter.activate()
				
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        return 0

downloader = Downloader()
sys.exit(downloader.main(sys.argv))






