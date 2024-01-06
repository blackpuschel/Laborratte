#!/usr/bin/env pybricks-micropython
import struct
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, ColorSensor, InfraredSensor, GyroSensor)
from pybricks.nxtdevices import (UltrasonicSensor, SoundSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
from threading import Thread
import math
import socket
import json
from timeit import default_timer


# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.

JSON_PATH = "./adresses.json"
SPEED = -50
TURN_ANGLE = -5
IFRS_TOLERANCE = 0
MAX_DISTANCE_FROM_WALL = 140

ev3 = EV3Brick()

motorLeft = Motor(Port.A)
motorRight = Motor(Port.B)

soundSensor = SoundSensor(Port.S2)
infraredSensor = InfraredSensor(Port.S3)
ultrasonsicSensor = UltrasonicSensor(Port.S4)

robot = DriveBase(motorLeft, motorRight, wheel_diameter=32.1, axle_track=175)

nodes = [(0, 0)]
initial_distance = -1
turn_assurance = 0
is_connected = False
timer_running = False
start_time = -1
sent_nodes = 0
available_nodes = 1

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

addresses = []
with open(JSON_PATH, 'r') as file:
    addresses = json.load(file)

def try_connecting():
    global is_connected
    for address in addresses:
        add = addresses[address]
        host = add[0]
        port = add[1]
        try:
            s.connect((host, port))
            is_connected = True
            print("Successfully connected to " + host + ":" + str(port))
            return
        except socket.error:
            print("Failed to connect to " + host + ":" + str(port))
            
    is_connected = False

def get_data_bytes():
    global sent_nodes

    byte_values = bytearray()
    unsent_nodes = nodes[sent_nodes:]

    sent_nodes = len(nodes)
    
    for node in unsent_nodes:
        byte_values.extend(struct.pack('dd', node[0], node[1]))
    return byte_values

def data_thread():
    global sent_nodes
    while True:
        while not is_connected:
            try_connecting()
            if not is_connected:
                wait(1000)
        
        data = get_data_bytes()
        if len(data) > 0: 
            s.sendall(data)
        wait(1000)

d_thread = Thread(target=data_thread)
d_thread.start()

def get_position():
    distance = robot.distance()
    angle = robot.angle()
    robot.reset()

    y = distance * math.sin(angle)
    x = math.sqrt(distance**2 - y**2)

    last_pos = nodes[-1]
    return (last_pos[0] + x, last_pos[1] + y)

def adjust_to_wall():
    global initial_distance
    global turn_assurance
    global timer_running
    global start_time

    if initial_distance < 0:
        initial_distance = infraredSensor.distance()
        if initial_distance > 40:
            initial_distance = -1
            if not timer_running:
                timer_running = True
                start_time = default_timer()

            duration = default_timer() - start_time
            if duration > 5:
                timer_running = False
                return False

        return True

    delta = infraredSensor.distance() - initial_distance

    wall_is_gone = delta > 10

    if wall_is_gone:
        turn_assurance += 1
    else:
        turn_assurance = 0

    if turn_assurance >= 10:
        turn_assurance = 0
        initial_distance = -1
        return False

    sways_right = delta > 0
    sways_left = delta < 0
    if sways_right:
        robot.drive(SPEED, 1)
    elif sways_left:
        robot.drive(SPEED, -1)
    else:
        robot.drive(SPEED, 0)

    return True

#def get_wall_angle(distance1, distance2, angle):
#    numerator = distance2 - distance1 * math.cos(angle)
#    denominator = math.sqr(distance1 * distance1 + distance2 * distance2 - 2 * distance1 * distance2 * math.cos(angle))
#    return math.acos(numerator / denominator)

#def align_to_wall():
#    distance1 = ultrasonsicSensor.distance()
#    robot.turn(TURN_ANGLE)
#    distance2 = ultrasonsicSensor.distance()
#
#    overshot = distance2 > distance1 * 2
#
#    if overshot:
#        distance2 = distance1
#        robot.turn(TURN_ANGLE * -2)
#        distance1 = ultrasonsicSensor.distance()
#
#    turn_angle = get_wall_angle(distance1, distance2, TURN_ANGLE)
#
#    robot.turn(turn_angle)

def take_measurements(amount):
    total_distance = 0
    out_of_ranges = 0
    for _ in range(amount):
        distance = ultrasonsicSensor.distance()
        total_distance += distance
        if distance == 255:
            out_of_ranges += 1

    ratio = out_of_ranges / amount
    if ratio < 0.5:
        total_distance -= out_of_ranges * 255
        amount -= out_of_ranges

    return total_distance / amount

def align_to_wall():
    while take_measurements(5) < 255:
        robot.turn(-5)

    lowest_measurement = 100
    higher_measurements = 0
    while higher_measurements < 3:
        current_measurement = infraredSensor.distance()
        if current_measurement < lowest_measurement:
            lowest_measurement = current_measurement
            higher_measurements = 0
        else:
            higher_measurements += 1

        robot.turn(-5)

    while infraredSensor.distance() > lowest_measurement + IFRS_TOLERANCE:
        robot.turn(5)

while ultrasonsicSensor.distance() > MAX_DISTANCE_FROM_WALL:
    robot.drive(SPEED, 0)

while True:
    initial_distance = -1
    timer_running = False

    nodes.append(get_position())
    align_to_wall()
    robot.drive(SPEED, 0)
    while ultrasonsicSensor.distance() > MAX_DISTANCE_FROM_WALL:
        next_to_wall = adjust_to_wall()
        wait(100)
        if not next_to_wall:
            wait(1000)
            nodes.append(get_position())
            robot.turn(90)
            robot.drive(SPEED, 0)

    turn_assurance = 0
    robot.stop()
    wait(200)
    