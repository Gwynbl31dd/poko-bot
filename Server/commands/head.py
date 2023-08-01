from Servo import Servo
from commands.command import Command


class Head(Command):

    def __init__(self, servo: Servo):
        print("Head build")

    def run(self, data: list):
        print("Head")
