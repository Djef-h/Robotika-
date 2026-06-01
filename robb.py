import sys
import time
import board
import busio
import adafruit_bno055
import math
from buildhat import MotorPair, Motor
from gpiozero import Button, LED

# ═══════════════════════════════════════════════════════
# ИЗКЛЮЧЕНИЯ
# ═══════════════════════════════════════════════════════

class MissionAbortException(Exception):
    pass

# ═══════════════════════════════════════════════════════
# ХАРДУЕР — БУТОНИ И LED (Обикновени GPIO компоненти)
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
# КЛАС DRIVEBASE (Управление на движението и жироскопа)
# ═══════════════════════════════════════════════════════

class Drivebase:
    def __init__(self, left_port='A', right_port='D'):
        # І2С връзка с жироскопа
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bno055.BNO055_I2C(i2c)
        
        # Превключване в IMU режим (само жироскоп + акселерометър)
        self.sensor.mode = adafruit_bno055.IMU_MODE
        time.sleep(0.5)

        self.motors = MotorPair(left_port, right_port)

        # Плавни рампи (ускорение) през Build HAT
        self.motors.primary.ramp_up_time = 0.3
        self.motors.primary.ramp_down_time = 0.3
        self.motors.secondary.ramp_up_time = 0.3
        self.motors.secondary.ramp_down_time = 0.3

        self.turn_tolerance  = 1
        self.default_speed   = 30
        self.wheel_diameter_cm = 5.5
        self.axle_track_cm     = 11.0

    def check_emergency_stop(self):
        if button_cancel.is_pressed:
            print("\n[--- CANCEL ---] Прекъсване!")
            self.stop()
            raise MissionAbortException()

    def _get_heading(self):
        try:
            return self.sensor.euler[0]
        except:
            return None

    def _angle_error(self, current, target):
        return (target - current + 540) % 360 - 180

    def stop(self):
        self.motors.stop()

    def move_cm(self, distance_cm, speed=None):
        if speed is None:
            speed = self.default_speed

        wheel_circumference = self.wheel_diameter_cm * math.pi
        rotations = distance_cm / wheel_circumference
        target_degrees = abs(math.floor(rotations * 360))

        start_pos_left = abs(self.motors.primary.position)
        
        if distance_cm > 0:
            self.motors.start(speed, -speed)
        else:
            self.motors.start(-speed, speed)

        while True:
            self.check_emergency_stop()
            current_pos_left = abs(self.motors.primary.position)
            if abs(current_pos_left - start_pos_left) >= target_degrees:
                break
            time.sleep(0.015)

        self.stop()

    # ---------------- TURN TWO WHEELS (Относителен завой) ----------------

    def turn_two_wheels(self, angle, speed):
        """
        Завърта робота на определен ъгъл СПРЯМО СЕГАШНАТА му позиция.
        Пример: turn_two_wheels(-90, 40) завърта робота на 90 градуса наляво.
        """
        start = self._get_heading()
        if start is None:
            start = 0
            
        # Изчисляваме крайната цел спрямо текущия ъгъл
        target = (start + angle) % 360
        
        # Определяме посоката на въртене на моторите спрямо знака на angle (+ или -)
        direction = 1 if angle > 0 else -1

        start_time = time.time()
        self.motors.start(direction * speed, direction * speed)

        while True:
            self.check_emergency_stop()
            
            # Защита от забиване (Timeout)
            if time.time() - start_time > 4.0:
                print("[ВНИМАНИЕ] Завоят прекратен поради изтичане на времето!")
                break

            current = self._get_heading()
            if current is None:
                continue
                
            if abs(self._angle_error(current, target)) < self.turn_tolerance:
                break
                
            time.sleep(0.015)

        self.stop()

# ═══════════════════════════════════════════════════════
# СЪСТЕЗАТЕЛНИ РЪНОВЕ (МИСИИ)
# ═══════════════════════════════════════════════════════

def mission_1(robot, motorLeft, motorRight):
    robot.move_cm(77, speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(-90, speed=40)  # Завърта се на точно 90 градуса наляво от мястото си
    time.sleep(0.1)
    robot.move_cm(20, speed=60)
    robot.stop()

def mission_2(robot, motorLeft, motorRight):
    robot.move_cm(30, speed=60)
    time.sleep(0.1)
    robot.turn_two_wheels(90, speed=40)   # Завърта се на точно 90 градуса надясно от мястото си
    time.sleep(0.1)
    robot.stop()

def mission_3(robot, motorLeft, motorRight):
    pass

def mission_4(robot, motorLeft, motorRight):
    pass

def mission_5(robot, motorLeft, motorRight):
    pass
   
def mission_6(robot, motorLeft, motorRight):
    pass

def mission_7(robot, motorLeft, motorRight):
    pass

def mission_8(robot, motorLeft, motorRight):
    pass

MISSIONS = {
    0: mission_1, 1: mission_2, 2: mission_3, 3: mission_4,
    4: mission_5, 5: mission_6, 6: mission_7, 7: mission_8,
}

# ═══════════════════════════════════════════════════════
# ГЛАВНА ФУНКЦИЯ (MAIN)
# ═══════════════════════════════════════════════════════

def main():
    print("[СТАРТ] Инициализация на робота...")
    robot      = Drivebase('A', 'D')
    motorLeft  = Motor(port='B')
    motorRight = Motor(port='C')
    time.sleep(1)
    print("[ГОТОВ] Роботът е готов в IMU режим.")

    selected = 0

    try:
        while True:
            update_leds(selected)
            print(f"\n[МЕНЮ] Рунд: {selected + 1} | UP = Смяна | OK = СТАРТ")

            while True:
                try:
                    if check_button_hold(button_up):
                        selected = (selected + 1) % COUNT_OF_MISSIONS
                        update_leds(selected)
                    elif button_ok.is_pressed:
                        wait_button_release(button_ok)
                        blink_led(selected)
                        break
                    time.sleep(0.05)
                except KeyboardInterrupt:
                    return

            try:
                mission_fn = MISSIONS.get(selected)
                if mission_fn:
                    print(f"\n[ИЗПЪЛНЕНИЕ] Стартиране на Рън {selected + 1}...")
                    mission_fn(robot, motorLeft, motorRight)
                    print(f"[УСПЕХ] Рън {selected + 1} завърши!")
                selected = (selected + 1) % COUNT_OF_MISSIONS
            except MissionAbortException:
                print(f"[ОТМЕНЕН] Рън {selected + 1} прекъснат.")

            time.sleep(0.5)

    finally:
        print("\n[КРАЙ] Освобождаване на GPIO пиновете...")
        button_ok.close()
        button_cancel.close()
        button_up.close()
        for led in leds:
            led.close()
        sys.exit(0)

if __name__ == "__main__":
    main()