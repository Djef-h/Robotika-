import sys
import time
import board
import busio
import adafruit_bno055
import threading
import math
from buildhat import MotorPair, Motor
from gpiozero import Button, LED


# ═══════════════════════════════════════════════════════
# ИЗКЛЮЧЕНИЯ
# ═══════════════════════════════════════════════════════

class MissionAbortException(Exception):
    pass


# ═══════════════════════════════════════════════════════
# ХАРДУЕР — БУТОНИ И LED
# ═══════════════════════════════════════════════════════

button_ok     = Button(21, pull_up=True)
button_cancel = Button(27, pull_up=True)
button_up     = Button(18, pull_up=True)

leds = [
    LED(22), LED(23), LED(24), LED(25), LED(5),
    LED(6),  LED(13), LED(19), LED(26), LED(20),
]

COUNT_OF_MISSIONS = 8



# ═══════════════════════════════════════════════════════
# ПОМОЩНИ ФУНКЦИИ ЗА МЕНЮТО
# ═══════════════════════════════════════════════════════

def update_leds(active_index):
    for i, led in enumerate(leds):
        led.on() if i == active_index else led.off()

def blink_led(index, times=3, delay=0.1):
    for _ in range(times):
        leds[index].off(); time.sleep(delay)
        leds[index].on();  time.sleep(delay)

def wait_button_release(button, debounce=0.05):
    while button.is_pressed:
        time.sleep(debounce)

def check_button_hold(button):
    if not button.is_pressed:
        return False
    wait_button_release(button)
    return True


# ═══════════════════════════════════════════════════════
# DRIVEBASE
# ═══════════════════════════════════════════════════════

class Drivebase:
    def __init__(self, left_port='A', right_port='D'):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bno055.BNO055_I2C(i2c)

        self.motors = MotorPair(left_port, right_port)

        self.turn_tolerance  = 1
        self.default_speed   = 30
        self.wheel_diameter_cm = 5.5
        self.axle_track_cm     = 11.0

    # ---------------- EMERGENCY STOP ----------------

    def check_emergency_stop(self):
        if button_cancel.is_pressed:
            print("\n[--- CANCEL ---] Мисията е прекъсната!")
            self.motors.stop()
            raise MissionAbortException()

    # ---------------- GYRO ----------------

    def _get_heading(self):
        try:
            return self.sensor.euler[0]
        except:
            return None

    def _angle_error(self, current, target):
        return (target - current + 540) % 360 - 180

    # ---------------- STOP ----------------

    def stop(self):
        self.motors.stop()

    # ---------------- MOVE ----------------

    def move_cm(self, distance_cm, speed=None):
        if speed is None:
            speed = self.default_speed

        wheel_circumference = self.wheel_diameter_cm * math.pi
        rotations = distance_cm / wheel_circumference
        degrees = math.floor(rotations * 360)

        self.motors.run_for_degrees(
            degrees,
            speedl=speed,
            speedr=-speed
        )

    # ---------------- TURN TWO WHEELS ----------------

    def turn_two_wheels(self, angle, speed):
        start     = self._get_heading()
        target    = (start + angle) % 360
        direction = 1 if angle > 0 else -1

        self.motors.start(direction * speed, direction * speed)

        while True:
            self.check_emergency_stop()
            current = self._get_heading()
            if current is None:
                continue
            if abs(self._angle_error(current, target)) < self.turn_tolerance:
                break
            time.sleep(0.005)

        self.stop()

    # ---------------- TURN ONE WHEEL ----------------

    def turn_one_wheel(self, angle, speed=30):
        start  = self._get_heading()
        target = (start + angle) % 360

        if angle > 0:
            self.motors.start(speed, 0)
        else:
            self.motors.start(0, -speed)

        while True:
            self.check_emergency_stop()
            current = self._get_heading()
            if current is None:
                continue
            if abs(self._angle_error(current, target)) < self.turn_tolerance:
                break
            time.sleep(0.005)

        self.stop()


# ═══════════════════════════════════════════════════════
# МИСИИ
# ═══════════════════════════════════════════════════════

def mission_1(robot, motorLeft, motorRight):
    robot.move_cm(77, speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(285, speed=30)
    time.sleep(0.1)
    robot.move_cm(7, speed=60)
    time.sleep(0.1)
    robot.move_cm(-12,speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(25, speed=-30)
    time.sleep(0.1)
    robot.move_cm(36,speed=60)
    time.sleep(0.1)
    motorLeft.run_for_degrees(210, 55)
    time.sleep(0.1)
    robot.move_cm(-8,speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(340,speed=30)
    time.sleep(0.1)
    robot.move_cm(20, speed=60)
    #robot.turn_two_wheels(20,speed=-30)
    time.sleep(0.1)
    motorRight.run_for_degrees(210, -55)
    time.sleep(0.1)
    robot.move_cm(3, speed=60)
    time.sleep(0.1)
    robot.move_cm(-44,speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(-95,speed=-30)
    time.sleep(0.1)
    robot.move_cm(110, speed=60)

    """
    robot.move_cm(5, speed=-50)
    robot.turn_two_wheels(-330, speed=30)
    robot.move_cm(8, speed=50)
    robot.move_cm(9, speed=60)
    robot.turn_two_wheels(-10, speed=-30)
    robot.move_cm(8, speed=-50)
    robot.turn_two_wheels(-36, speed=-30)
    robot.move_cm(34, speed=-60)
    robot.move_cm(28, speed=80)
    robot.turn_two_wheels(35, speed=-30)
    robot.move_cm(69, 80)
    """
    robot.stop()

def mission_5(robot, motorLeft, motorRight):
    robot.move_cm(20, speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(330, speed=30)
    time.sleep(0.1)
    robot.move_cm(8, speed=-60)
    time.sleep(0.1)
    robot.turn_two_wheels(315, speed=30)
    time.sleep(0.1)
    robot.move_cm(25, speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(330, speed=30)
    time.sleep(0.1)
    robot.move_cm(28, speed=60)
    time.sleep(0.1)
    motorLeft.run_for_degrees(210, 55)
    time.sleep(0.1)
    robot.move_cm(12, speed=-60)
    time.sleep(0.1)
    motorRight.run_for_degrees(210, -55)
    time.sleep(0.1)
    robot.move_cm(7, speed=-60)
    time.sleep(0.1)
    robot.turn_two_wheels(45, speed=-30)
    time.sleep(0.1)
    robot.move_cm(27, speed=-60)
    """
    robot.move_cm(-9,speed=60)
    time.sleep(0.4)
    robot.turn_two_wheels(30, speed=-30)
    time.sleep(0.4)
    robot.move_cm(40,speed=60)
    time.sleep(0.4)
    motorLeft.run_for_degrees(210, 55)
    time.sleep(0.4)
    robot.move_cm(-10,speed=60)
    time.sleep(0.4)
    robot.turn_two_wheels(335,speed=30)
    time.sleep(0.4)
    robot.move_cm(20, speed=60)
    robot.turn_two_wheels(345,speed=30)
    time.sleep(0.4)
    motorRight.run_for_degrees(210, -55)
    time.sleep(0.4)
    robot.move_cm(7, speed=60)
    time.sleep(0.4)
    robot.move_cm(-35,speed=60)
    time.sleep(0.4)
    robot.turn_two_wheels(-87,speed=-30)
    time.sleep(0.4)
    robot.move_cm(100, speed=60)
    """
    robot.stop()
   

def mission_2(robot, motorLeft, motorRight):
    robot.move_cm(65, speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(-350, speed=30)
    time.sleep(0.1)
    robot.move_cm(5, speed=-60)
    time.sleep(0.1)
    robot.turn_two_wheels(290, speed=30)
    time.sleep(0.1)
    robot.move_cm(5, speed=60)
    time.sleep(0.1)
    motorRight.run_for_degrees(210, 55)
    time.sleep(0.1)
    robot.move_cm(9, speed=-60) 
    time.sleep(0.1)
    robot.turn_two_wheels(-300, speed=30)
    time.sleep(0.1)
    robot.move_cm(60, speed=-60)

def mission_4(robot, motorLeft, motorRight):
    robot.move_cm(65, speed=60)
    time.sleep(0.1) 
    robot.turn_two_wheels(300, speed=30)
    time.sleep(0.1)
    robot.move_cm(4, speed=60)
    time.sleep(0.1)
    robot.move_cm(-9,speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(60, speed=-30)
    time.sleep(0.1)
    robot.move_cm(58,speed=-60)
    robot.stop()
def mission_6(robot, motorLeft, motorRight):
    """
    robot.turn_two_wheels(-310, speed=30)
    time.sleep(0.1)
    robot.turn_two_wheels(320, speed=30)
    time.sleep(0.1)
    """
    robot.move_cm(17, speed=60)
    time.sleep(0.1)
    robot.move_cm(17, speed=-60)

def  mission_7(robot, motorLeft, motorRight):
    motorRight.run_for_degrees(200, 100)

def  mission_8(robot, motorLeft, motorRight):
    motorRight.run_for_degrees(200, 100)

def mission_3(robot, motorLeft, motorRight):
    robot.move_cm(75, speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(279, speed=30)
    time.sleep(0.1)
    robot.move_cm(17, speed=60)
    time.sleep(0.1)
    robot.move_cm(8, speed=10)
    time.sleep(0.1)
    robot.move_cm(-21,speed=60)
    time.sleep(0.1)
    """
    robot.turn_two_wheels(90, speed=30)
    time.sleep(0.1)
    robot.move_cm(30,speed=50)
    time.sleep(0.1)
    robot.turn_two_wheels(270, speed=-30)
    time.sleep(0.1)
    robot.move_cm(30, speed=40)
    time.sleep(0.1)
    """
    
    robot.turn_two_wheels(76, speed=-30)
    time.sleep(0.1)
    robot.move_cm(55,speed=-60)
    robot.stop()


MISSIONS = {
    0: mission_1,
    1: mission_2,
    2: mission_3,
    3: mission_4,
    4: mission_5,
    5: mission_6,
    6: mission_7,
    7: mission_8,
}


# ═══════════════════════════════════════════════════════
# ГЛАВЕН ЦИКЪЛ
# ═══════════════════════════════════════════════════════

def main():
    print("[СТАРТ] Инициализация на робота...")
    robot      = Drivebase('A', 'D')
    motorLeft  = Motor(port='B')
    motorRight = Motor(port='C')
    time.sleep(1)
    print("[ГОТОВ] Робота е готов.")

    selected = 0

    while True:
        update_leds(selected)
        print(f"\n[МЕНЮ] Мисия {selected + 1} | UP = следваща | OK = старт")

        while True:
            try:
                if check_button_hold(button_up):
                    selected = (selected + 1) % COUNT_OF_MISSIONS
                    update_leds(selected)
                    print(f"[МЕНЮ] → Мисия {selected + 1}")
                elif button_ok.is_pressed:
                    wait_button_release(button_ok)
                    blink_led(selected)
                    break
                time.sleep(0.05)
            except KeyboardInterrupt:
                print("\n[ИЗХОД] Ctrl+C — програмата спира.")
                update_leds(-1)
                sys.exit(0)

        try:
            mission_fn = MISSIONS.get(selected)
            if mission_fn:
                print(f"\n[СТАРТ] Мисия {selected + 1} започва...")
                mission_fn(robot, motorLeft, motorRight)
                print(f"[УСПЕХ] Мисия {selected + 1} завърши!")
            else:
                print(f"[ГРЕШКА] Мисия {selected + 1} не е дефинирана.")
            selected = (selected + 1) % COUNT_OF_MISSIONS
        except MissionAbortException:
            print(f"[ОТМЕНЕНА] Мисия {selected + 1} прекъсната — обратно в менюто.")

        time.sleep(0.5)


if __name__ == "__main__":
    main()