#!/usr/bin/env python3

import os
from Server import Server
from Servo import Servo
from Control import Control
from commands.head import Head
from commands.command import Command
from commands.camera import Camera


class App():

    def __init__(self, servo: Servo, control: Control):
        self.servo = servo
        self.control = control
        commands = self.get_commands()
        self.server = Server(commands, self.servo, self.control)

    def run(self):
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.server.stop()
            os._exit(0)

    def get_commands(self) -> dict:
        commands = {}
        self._add_commands_head(commands)
        self._add_commands_camera(commands)
        return commands

    def _add_commands_head(self, commands: dict):
        commands[Command.CMD_HEAD] = []
        commands[Command.CMD_HEAD].append(Head(servo))

    def _add_commands_camera(self, commands: dict):
        commands[Command.CMD_CAMERA] = []
        commands[Command.CMD_CAMERA].append(Camera(self.servo, self.control))


if __name__ == '__main__':
    servo = Servo()
    control = Control()
    app = App(servo, control)
    app.run()
