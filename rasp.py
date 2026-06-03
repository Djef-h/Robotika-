from copy import error
import sys
import time
import board
import busio
import adafruit_bno055
import math
from buildhat import MotorPair, Motor
from gpiozero import Button, LED

button_ok     = Button(21, pull_up=True)
button_cancel = Button(27, pull_up=True)
button_up     = Button(18, pull_up=True)

class Mehano:
    def __init__(self):
        # BNO055
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bno055.BNO055_I2C(self.i2c)
        
        self.sensor.mode = adafruit_bno055.IMUPLUS_MODE
        time.sleep(0.2)
    
        self.motors = MotorPair('A', 'B')
        self.motor_left = Motor('A')
        self.motor_right = Motor('B')
        self.motor_left_atach = Motor('C')
        self.motor_right_atach = Motor('D')
        
    def calibrate(self):
        sys,gyro,accel = self.sensor.calibration_status
        self.sys = sys
        self.gyro = gyro
        self.accel = accel 

        if sys == 3 and gyro == 3 and accel == 3:
            return True
        else:
            return False
        
    def get_orientation(self):
        yaw, roll, pitch = self.sensor.euler
        if yaw is not None:
            self.yaw = yaw
            self.roll = roll
            self.pitch = pitch
        
    def stop(self):
        self.motors.stop()
        self.motor_left.stop()
        self.motor_right.stop()
                
    def read_accel(self):
        x, y, z = self.sensor.acceleration
        self.x = x
        self.y = y
        self.z = z

    def turn(self, angle,speed):
        self.get_orientation()
        start_heading = self.yaw
        target_heading = (start_heading + angle) % 360
        error = (target_heading - self.yaw + 540) % 360 - 180
        
        while abs(error) >= 1.5:
            self.get_orientation()
            error = (target_heading - self.yaw + 540) % 360 - 180 
            
            minimal_speed = min(speed, abs(error))
            turn_speed = max(minimal_speed, 15)
            
            if error > 0:
                self.motors.start(turn_speed, -turn_speed)
            else:
                self.motors.start(-turn_speed, turn_speed)
            
        self.stop()
        
    def move_forward(self, distance, speed):
        self.get_orientation()
        wheel_d = 5.6
        wheel = wheel_d * math.pi
        degrees = (distance * 360) / wheel
        
        self.motor_left_position = self.motor_left.get_position()
        self.motor_right_position = self.motor_right.get_position()
        self.average_start_position = (self.motor_left_position + self.motor_right_position) / 2
        self.target_position = self.average_start_position + degrees
        
        accel = 100
        decel = 200
        min_speed = 15 
    
        degr_left = degrees
            
            
        while degr_left >= 1.5:
            self.get_orientation()
            self.motor_left_position = self.motor_left.get_position()
            self.motor_right_position = self.motor_right.get_position()
            self.average_position = (self.motor_left_position + self.motor_right_position) / 2
            
            degr_traveled = self.average_position - self.average_start_position
            degr_left = self.target_position - self.average_position
            
            if degr_traveled < accel:
                x = degr_traveled / accel
                current_speed = min_speed + (speed - min_speed) * x
            elif  degr_left < decel:
                x = degr_left / decel
                current_speed = min_speed + (speed - min_speed) * x
            else:
                current_speed = speed
            
            current_speed = max(min(current_speed, speed), min_speed)
            
            self.motors.start(current_speed, current_speed)
        self.stop()
        
