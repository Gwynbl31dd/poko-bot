from Control import Control
from Servo import Servo
from commands.command import Command

import logging

logging.basicConfig(level=logging.INFO)


class Camera(Command):

    def __init__(self, servo: Servo, control: Control):
        self.servo = servo
        self.control = control
        logging.info("Camera build")

    def run(self, data: list):
        if len(data) == 3:
            x = self.control.restriction(int(data[1]), 50, 180)
            y = self.control.restriction(int(data[2]), 0, 180)
            self.servo.setServoAngle(0, x)
            self.servo.setServoAngle(1, y)
