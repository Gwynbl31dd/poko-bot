from Control import Control
from Servo import Servo
from commands.command import Command

import logging

logging.basicConfig(level=logging.INFO)


class Camera(Command):

    def __init__(self, control: Control, servo: Servo):
        logging.info("Camera build")

    def run(self, data: list):
        logging.info("Camera")
