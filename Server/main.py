#!/usr/bin/env python3

import os
from Server import Server
from Servo import Servo
from commands.head import Head
from commands.command import Command

class App():

    def __init__(self):
        commands = self.get_commands()
        self.server=Server(commands)
            
    def run(self):
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.server.stop()
            os._exit(0)
            
    def get_commands(self) -> dict:
        commands = {}
        servo = Servo()
        commands[Command.CMD_HEAD] = Head(servo)
        return commands
        
if __name__ == '__main__':
    app = App()
    app.run()

