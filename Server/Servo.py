from PCA9685 import PCA9685
import time 
import math
import smbus

def mapNum(value,fromLow,fromHigh,toLow,toHigh):
    return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow

class Servo:
    def __init__(self):
        self.pwm_40 = PCA9685(0x40, debug=True)
        self.pwm_41 = PCA9685(0x41, debug=True)
        # Set the cycle frequency of PWM  
        self.pwm_40.setPWMFreq(50) 
        time.sleep(0.01) 
        self.pwm_41.setPWMFreq(50) 
        time.sleep(0.01)             

    #Convert the input angle to the value of pca9685
    def setServoAngle(self,channel, angle):  
        if channel < 16:
            date = mapNum(mapNum(angle,0,180,500,2500),0,20000,0,4095) # 0-180 map to 500-2500us ,then map to duty 0-4095
            self.pwm_41.setPWM(channel, 0, int(date))
        elif channel >= 16 and channel < 32:
            channel-=16
            date = mapNum(mapNum(angle,0,180,500,2500),0,20000,0,4095) # 
            self.pwm_40.setPWM(channel, 0, int(date))

    def relax(self):
        for i in range(8):
            self.pwm_41.setPWM(i+8, 4096, 4096)
            self.pwm_40.setPWM(i, 4096, 4096)
            self.pwm_40.setPWM(i+8, 4096, 4096)