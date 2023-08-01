#!/usr/bin/env python3

import os
from Server import Server
from Servo import Servo
from Control import Control
from commands.head import Head
from commands.command import Command
from commands.camera import Camera


class App():

    def __init__(self):
        servo = Servo()
        control = Control()
        commands = self.get_commands(servo, control)
        self.server = Server(commands, servo, control)

    def run(self):
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.server.stop()
            os._exit(0)

    def get_commands(self, servo: Servo, control: Control) -> dict:
        commands = {}
        self._add_commands_head(servo, commands)
        self._add_commands_camera(servo, control, commands)
        return commands

    def _add_commands_head(self, servo: Servo, commands: dict):
        commands[Command.CMD_HEAD] = []
        commands[Command.CMD_HEAD].append(Head(servo))

    def _add_commands_camera(self, servo: Servo, control: Control, commands: dict):
        commands[Command.CMD_CAMERA] = []
        commands[Command.CMD_CAMERA].append(Camera(servo, control))


if __name__ == '__main__':
    app = App()
    app.run()
