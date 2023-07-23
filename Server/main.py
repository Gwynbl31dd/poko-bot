#!/usr/bin/env python3

import os
import sys,getopt
from Server import *
from Control import *
import logging

class App():

    def __init__(self):
        self.server=Server()
            
    def run(self):
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.server.stop()
            os._exit(0)
        
if __name__ == '__main__':
    app = App()
    app.run()

