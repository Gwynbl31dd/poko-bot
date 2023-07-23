#!/usr/bin/env python3

import os
import sys,getopt
from Server import *
from Control import *
import logging

class App():

    def __init__(self):
        self.server=Server()

    def stop_server(self):
        self.server.stop()
        try:
            stop_thread(self.video)
            stop_thread(self.instruction)
            self.server.server_socket.shutdown(2)
            self.server.server_socket1.shutdown(2)
        except Exception as e:
            logging.warning(e)
            
    def run(self):
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.stop_server()
            os._exit(0)
        
if __name__ == '__main__':
    app = App()
    app.run()

