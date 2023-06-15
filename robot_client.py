#!/usr/bin/env python3

from robots import robots, server_none, server_york

import asyncio
import websockets
import json
import signal
import time
import sys
from enum import Enum
import time
import random
import inspect
from vector2d import Vector2D
import math
import pprint
import angles
import colorama
from colorama import Fore

"""
This function is the main loop of your application. You can make any changes you want throughout this 
file, but most of your game logic will be located in here.

First, ensure that the robot_ids list below is correctly set to the robots you wish to work with.
For example:
    robot_ids = [34, 37, 39]

When run, this script will connect to the server and then repeatedly call the main_loop() function.
The script communicates with the robots using a websockets connection. Sending data requires that you 
use Python's asynchronous I/O. If you are not familiar with this, the rule is to remember that the control
function should be declared with "async" (see the simple_obstacle_avoidance() example) and called from 
main_loop() using loop.run_until_complete(async_thing_to_run(ids))
"""

robot_ids = [35]


def main_loop():
    # This requests all virtual sensor data from the tracking server for the robots specified in robot_ids
    # This is stored in the global variable active_robots, a map of id -> instances of the Robot class (defined lower in this file)
    print(Fore.GREEN + "[INFO]: Requesting data from tracking server")
    loop.run_until_complete(get_server_data())

    # Request sensor data from detected robots
    # This augments the Robot instances with their battery level and the values from each robot's proximity sensors
    # You only need to do this if you care about their battery level, or are using their proximity sensors
    print(Fore.GREEN + "[INFO]: Robots detected:", ids)
    print(Fore.GREEN + "[INFO]: Requesting data from detected robots")
    loop.run_until_complete(get_robot_data(ids))

    # Now run our behaviour
    print(Fore.GREEN + "[INFO]: Sending commands to detected robots")
    loop.run_until_complete(send_robot_commands(ids))

    print()

    # Sleep until next control cycle. We use 0.1 seconds by default so as to not flood the network.
    time.sleep(0.1)


"""
This is an example of a behaviour. You will want to replace this with a behaviour that implements your team
movements. It currently is an example of basic object avoidance.
This function is called for each robot that we listed in robot_ids that we are interested in.
"""


async def send_commands(robot):
    print(
        f"Commanding robot {robot.id}: Team {robot.team}, Role {robot.role}, Orientation {robot.orientation}")

    """
    robot.neighbours is a map of all the other robots (i.e. not this one) 
    with their role, team, range from this robot, and bearing from this robot
    For example:
    { '33': { 'bearing': -178.98,
              'orientation': -16.26,
              'range': 1.14,
              'role': 'NOMAD',
              'team': 'UNASSIGNED'},
      '34': { 'bearing': 177.24,
              'orientation': -25.56,
              'range': 1.47,
              'role': 'DEFENDER',
              'team': 'BLUE'},

    Print it with pprint.PrettyPrinter(indent=2).pprint(robot.neighbours)
    """

    try:
        # Turn off LEDs and motors when killed. Please do this!
        if kill_now():
            message = {"set_leds_colour": "off", "set_motor_speeds": {}}
            message["set_motor_speeds"]["left"] = 0
            message["set_motor_speeds"]["right"] = 0
            await robot.connection.send(json.dumps(message))

        message = {}
        message["set_motor_speeds"] = {}

        """
        Construct a command message
        Robots are controlled by sending them a JSON dictionary which we create here using the message variable
        
        We can set the speed of the wheel motors (from -100 to 100). Setting them to the same value makes the robot go forwards
        or backwards. Setting them differently makes the robot turn. For example:
        message["set_motor_speeds"]["left"] = 100
        message["set_motor_speeds"]["right"] = 100
    
        We can also set the colour of the LED. Supported colours are "off", "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"
        message["set_leds_colour"] = "green"

        You can combine commands (i.e. setting both wheels and the LED colour in one go)

        The rest of this function is an example object avoidance behaviour which goes FORWARD unless the IR sensor
        detects something in front of it, when it will turn instead.
        Then every 5 seconds it attempts to regroup the robots by turning them towards the average bearing of all other robots.
        """
        # if robot.state == RobotState.FORWARDS:
        #     left = right = robot.MAX_SPEED
        #     if (time.time() - robot.turn_time > 0.5) and any(ir > 80 for ir in robot.ir_readings):
        #         robot.turn_time = time.time()
        #         robot.state = random.choice((RobotState.LEFT, RobotState.RIGHT))
        #     elif (time.time() - robot.regroup_time > 5): # Every 5 seconds, go into the "regroup" state
        #         robot.regroup_time = time.time()
        #         robot.state = RobotState.REGROUP

        # elif robot.state == RobotState.BACKWARDS:
        #     left = right = -robot.MAX_SPEED
        #     robot.turn_time = time.time() #Note when we started turning
        #     robot.state = RobotState.FORWARDS

        # elif robot.state == RobotState.LEFT:
        #     left = -robot.MAX_SPEED
        #     right = robot.MAX_SPEED
        #     if time.time() - robot.turn_time > random.uniform(0.5, 1.0): #Ensure we've been turning for some amount of time
        #         robot.turn_time = time.time()
        #         robot.state = RobotState.FORWARDS

        # elif robot.state == RobotState.RIGHT:
        #     left = robot.MAX_SPEED
        #     right = -robot.MAX_SPEED
        #     if time.time() - robot.turn_time > random.uniform(0.5, 1.0):
        #         robot.turn_time = time.time()
        #         robot.state = RobotState.FORWARDS

        # #Robots are created in the STOP state
        # elif robot.state == RobotState.STOP:
        #     left = right = 0
        #     robot.turn_time = time.time()
        #     robot.state = RobotState.FORWARDS

        # In the regroup state, they try to group back together
        # This is an example of using the robot.neighbours map to set our target direction based on where other robots are.
        # It will get vectors to all other robots, average the direction, and so move the "middle" of the swarm
        # elif robot.state == RobotState.REGROUP:
        #     message["set_leds_colour"] = "green"

        #     target_direction = Vector2D(0, 0) #Create a zero vector to work with
        #     for neighbour_id, neighbour in robot.neighbours.items(): #For every other robot (you probably want to filter this by team/role)
        #
        #         vector_to_neighbour = Vector2D(neighbour["range"] * math.cos(math.radians(neighbour["bearing"])),
        #                                        neighbour["range"] * math.sin(math.radians(neighbour["bearing"])))

        #         target_direction += vector_to_neighbour #Add up all the neighbour vectors
        #     target_direction /= len(robot.neighbours) #Average them

        #     direction_polar = target_direction.to_polar() #By getting a polar vector, we get the target bearing
        #     #But that bearing is in radians, so we convert to degrees that are normalised to between 180 and -180, like this:
        #     heading = angles.normalize(math.degrees(direction_polar[1]), -180, 180)

        #     #Turn left or right based on the resulting angle
        #     if heading > 0:
        #         left = robot.MAX_SPEED
        #         right = 0
        #     else:
        #         left = 0
        #         right = robot.MAX_SPEED
        #     if time.time() - robot.regroup_time > random.uniform(3.0, 4.0): #Back into the FORWARDS state after a delay
        #         message["set_leds_colour"] = "red"
        #         robot.state = RobotState.FORWARDS

        # #This is an example state for moving towards the ball
        # elif robot.state == RobotState.TO_BALL:
        #     message["set_leds_colour"] = "yellow"
        #     if robot.distance_to_ball < 0.1:
        #         robot.state = RobotState.TO_OUR_GOAL
        #     if abs(robot.bearing_to_ball) < 20:
        #          left = right = robot.MAX_SPEED
        #     elif robot.bearing_to_ball > 0:
        #         left = int(float(robot.MAX_SPEED)/1.4) #If we do a "full speed turn" then they overshoot.
        #         right = -int(float(robot.MAX_SPEED)/1.4) #A good implementation would turn at a speed based on how misalaigned they are
        #     else:
        #         left = -int(float(robot.MAX_SPEED)/1.4)
        #         right = int(float(robot.MAX_SPEED)/1.4)

        # #This is an example state for moving towards our goal
        # elif robot.state == RobotState.TO_OUR_GOAL:
        #     if robot.distance_to_our_goal < 0.2:
        #         robot.state = RobotState.TO_THEIR_GOAL
        #     message["set_leds_colour"] = "cyan"
        #     if abs(robot.bearing_to_our_goal) < 20:
        #          left = right = robot.MAX_SPEED
        #     elif robot.bearing_to_our_goal > 0:
        #         left = int(float(robot.MAX_SPEED)/1.4)
        #         right = -int(float(robot.MAX_SPEED)/1.4)
        #     else:
        #         left = -int(float(robot.MAX_SPEED)/1.4)
        #         right = int(float(robot.MAX_SPEED)/1.4)

        # #This is an example state for moving towards their goal
        # elif robot.state == RobotState.TO_THEIR_GOAL:
        #     if robot.distance_to_their_goal < 0.2:
        #         robot.state = RobotState.TO_BALL
        #     message["set_leds_colour"] = "magenta"
        #     if abs(robot.bearing_to_their_goal) < 20:
        #          left = right = robot.MAX_SPEED
        #     elif robot.bearing_to_their_goal > 0:
        #         left = int(float(robot.MAX_SPEED)/1.4)
        #         right = -int(float(robot.MAX_SPEED)/1.4)
        #     else:
        #         left = -int(float(robot.MAX_SPEED)/1.4)
        #         right = int(float(robot.MAX_SPEED)/1.4)

        # message["set_motor_speeds"] = {}
        # message["set_motor_speeds"]["left"] = left
        # message["set_motor_speeds"]["right"] = right
        if robot.role == "DEFENDER":
            defender_commands(robot, message)
        elif robot.role == "MID_FIELD":
            midfield_commands(robot, message)

        # Send command message
        await robot.connection.send(json.dumps(message))

    except Exception as e:
        print(f"send_commands: {type(e).__name__}: {e}")


# Robot class and structures
# ----------------------------

# Robot states to use in the example controller. Feel free to change.
class RobotState(Enum):
    IDLE = 0
    STOP = 1

    #DEFENDER
    DEF_IDLE = IDLE
    DEF_STOP = STOP
    DEF_FACE_ENEMIES = 2
    DEF_TO_BALL = 3
    DEF_TO_OUR_GOAL = 4
    DEF_TO_THEIR_GOAL = 5
    DEF_INTERCEPT = 7

    #MID
    MID_IDLE = IDLE
    MID_STOP = STOP
    MID_TO_BALL = 8
    MID_TO_THEIR_BOUND = 9
    MID_MIMICBALL = 10
    MID_TO_OURBAND = 11
    MID_OURBAND_DEF = 12 
    MID_INTERCEPT = 13

    #ATT
    

# Main Robot class to keep track of robot states


class Robot:
    # Firmware on both robots accepts wheel velocities between -100 and 100.
    # This limits the controller to fit within that.
    MAX_SPEED = 100

    def __init__(self, robot_id):
        self.id = robot_id
        self.connection = None
        self.tasks = {}

        self.orientation = 0  # Our orientation from "up". 0 to 359
        # All other robots in the area (see format, above)
        self.neighbours = {}
        self.role = 'NOMAD'  # Will be NOMAD, DEFENDER, MID_FIELD, STRIKER
        self.team = 'UNASSIGNED'  # Will be UNASSIGNED, RED, BLUE
        self.remaining_time = 0  # Number of seconds left in the match
        self.bearing_to_ball = 0
        self.distance_to_ball = 0
        # Value between 0 and 1 for your x coordinate in your assigned zone. If < 0 or > 1 you are out of your zone. 1 means furthest from your goal.
        self.progress_through_zone = 0

        self.bearing_to_our_goal = 0
        self.distance_to_our_goal = 0
        self.bearing_to_their_goal = 0
        self.distance_to_their_goal = 0

        self.ir_readings = []
        self.battery_charging = False
        self.battery_voltage = 0
        self.battery_percentage = 0

        # These are used by the example behaviour. Feel free to change.
        self.state = RobotState.STOP
        self.turn_time = time.time()
        self.regroup_time = time.time()


# -----------------------------------------------------------------
# You probably don't need to change anything below here
# -----------------------------------------------------------------


active_robots = {}
ids = []


# Server address, port details, globals
# ---------------------------------------
server_address = server_york
server_port = 6000
robot_port = 6000

if len(server_address) == 0:
    raise Exception(f"Enter local tracking server address on line {inspect.currentframe().f_lineno - 6}, "
                    f"then re-run this script.")

server_connection = None
colorama.init(autoreset=True)


# Handle Ctrl+C termination
# https://stackoverflow.com/questions/2148888/python-trap-all-signals
# ---------------------------------------------------------------------
SIGNALS_TO_NAMES_DICT = dict((getattr(signal, n), n)
                             for n in dir(signal) if n.startswith('SIG') and '_' not in n)
# https://github.com/aaugustin/websockets/issues/124
__kill_now = False


def __set_kill_now(signum, frame):
    print('\nReceived signal:', SIGNALS_TO_NAMES_DICT[signum], str(signum))
    global __kill_now
    __kill_now = True


signal.signal(signal.SIGINT, __set_kill_now)
signal.signal(signal.SIGTERM, __set_kill_now)


def kill_now() -> bool:
    global __kill_now
    return __kill_now


# Connect to websocket server of tracking server
async def connect_to_server():
    uri = f"ws://{server_address}:{server_port}"
    connection = await websockets.connect(uri)

    print("Opening connection to server: " + uri)

    awake = await check_awake(connection)

    if awake:
        print("Server is awake")
        global server_connection
        server_connection = connection
    else:
        print("Server did not respond")


# Connect to websocket server running on each of the robots
async def connect_to_robots():
    for id in active_robots.keys():
        ip = robots[id]
        if ip != '':
            uri = f"ws://{ip}:{robot_port}"
            connection = await websockets.connect(uri)

            print("Opening connection to robot:", uri)

            awake = await check_awake(connection)

            if awake:
                print(f"Robot {id} is awake")
                active_robots[id].connection = connection
            else:
                print(f"Robot {id} did not respond")
        else:
            print(f"No IP defined for robot {id}")


# Check if robot is awake by sending the "check_awake" command to its websocket server
async def check_awake(connection):
    awake = False

    try:
        message = {"check_awake": True}

        # Send request for data and wait for reply
        await connection.send(json.dumps(message))
        reply_json = await connection.recv()
        reply = json.loads(reply_json)

        # Reply should contain "awake" with value True
        awake = reply["awake"]

    except Exception as e:
        print(f"{type(e).__name__}: {e}")

    return awake


# Ask a list of robot IDs for all their sensor data (proximity + battery)
async def get_robot_data(ids):
    await message_robots(ids, get_data)


# Send all commands to a list of robots IDs (motors + LEDs)
async def send_robot_commands(ids):
    await message_robots(ids, send_commands)


# Tell a list of robot IDs to stop
async def stop_robots(ids):
    await message_robots(ids, stop_robot)


# Send a message to a list of robot IDs
# Uses multiple websockets code from:
# https://stackoverflow.com/questions/49858021/listen-to-multiple-socket-with-websockets-and-asyncio
async def message_robots(ids, function):
    loop = asyncio.get_event_loop()
    tasks = []
    for id, robot in active_robots.items():
        if id in ids:
            tasks.append(loop.create_task(function(robot)))
    await asyncio.gather(*tasks)


# Get robots' virtual sensor data from the tracking server, for our active robots
async def get_server_data():
    try:
        global ids
        message = {"get_robots": True}

        # Send request for data and wait for reply
        await server_connection.send(json.dumps(message))
        reply_json = await server_connection.recv()
        reply = json.loads(reply_json)

        # Filter reply from the server, based on our active robots of interest
        filtered_reply = {int(k): v for (k, v) in reply.items()
                          if int(k) in active_robots.keys()}
        ids = list(filtered_reply.keys())

        pprint.PrettyPrinter(indent=4).pprint(reply)
        #print(f"active_robots.keys() = {active_robots.keys()}")
        #print(f"filtered_reply = {filtered_reply}")
        #print(f"ids = {ids}")

        # Receive robot virtual sensor data from the server
        for id, robot in filtered_reply.items():
            #print(f"Updating robot {id}")
            active_robots[id].orientation = robot["orientation"]
            active_robots[id].role = robot["role"]
            active_robots[id].team = robot["team"]
            active_robots[id].remaining_time = robot["remaining_time"]
            active_robots[id].neighbours = robot["players"]
            active_robots[id].bearing_to_ball = robot["ball"]["bearing"]
            active_robots[id].distance_to_ball = robot["ball"]["range"]
            active_robots[id].progress_through_zone = robot["progress_through_zone"]
            active_robots[id].bearing_to_our_goal = robot["our_goal"]["bearing"]
            active_robots[id].distance_to_our_goal = robot["our_goal"]["range"]
            active_robots[id].bearing_to_their_goal = robot["their_goal"]["bearing"]
            active_robots[id].distance_to_their_goal = robot["their_goal"]["range"]

    except Exception as e:
        print(f"get_server_data: {type(e).__name__}: {e}")


# Stop robot from moving and turn off its LEDs
async def stop_robot(robot):
    try:
        # Turn off LEDs and motors when killed
        message = {"set_leds_colour": "off", "set_motor_speeds": {}}
        message["set_motor_speeds"]["left"] = 0
        message["set_motor_speeds"]["right"] = 0
        await robot.connection.send(json.dumps(message))

        # Send command message
        await robot.connection.send(json.dumps(message))
    except Exception as e:
        print(f"{type(e).__name__}: {e}")


# Get IR and battery readings from robot
async def get_data(robot):
    try:
        message = {"get_ir": True, "get_battery": True}

        # Send request for data and wait for reply
        await robot.connection.send(json.dumps(message))
        reply_json = await robot.connection.recv()
        reply = json.loads(reply_json)

        robot.ir_readings = reply["ir"]
        robot.battery_voltage = reply["battery"]["voltage"]
        robot.battery_percentage = reply["battery"]["percentage"]

    except Exception as e:
        print(f"{type(e).__name__}: {e}")


def midfield_commands(robot: Robot, message):
    if robot.state == RobotState.MID_STOP:
        robot.state = RobotState.MID_INTERCEPT
        message["set_motor_speeds"]["left"] = 0
        message["set_motor_speeds"]["right"] = 0

    if(robot.state == RobotState.MID_TO_BALL):
        if (robot.progress_through_zone > 0.95) or (robot.progress_through_zone < 0.05):
            robot.state = RobotState.MID_OURBAND_DEF
        #print("TOBALL")
        #print(ball_Pos2Robot(robot.bearing_to_ball))
        go_to_ball(robot, message)
        pass
    
    if robot.state == RobotState.MID_TO_THEIR_BOUND:
        pass

    if robot.state == RobotState.MID_MIMICBALL:
        pass

    if robot.state == RobotState.MID_TO_OURBAND:
        pass

    if(robot.state == RobotState.MID_OURBAND_DEF):
        message["set_motor_speeds"]["left"] = 0
        message["set_motor_speeds"]["right"] = 0
        pass

    if robot.state == RobotState.MID_INTERCEPT:
        intercept_mid_field(robot, message)


def ball_Pos2Robot(angle):
    if math.cos(angle) >= 0:
        return True
    else:
        return False
    


# DEFENDER
def defender_commands(robot: Robot, message):
    print("Enemy bearing", robot.bearing_to_their_goal)
    if robot.state == RobotState.DEF_TO_OUR_GOAL:
        if robot.distance_to_ball <= 0.3 and robot.progress_through_zone < 0.6:
            robot.state = RobotState.DEF_INTERCEPT
        elif robot.distance_to_our_goal <= 0.05:
            robot.state = RobotState.DEF_FACE_ENEMIES
        return_to_goal(robot, message)

    elif robot.state == RobotState.DEF_TO_BALL:
        if robot.progress_through_zone > 0.9:
            robot.state = RobotState.DEF_TO_OUR_GOAL
        go_to_ball(robot, message)

    elif robot.state == RobotState.DEF_FACE_ENEMIES:
        face_forward(robot, message)

    elif robot.state == RobotState.DEF_STOP:
        robot.state = RobotState.DEF_TO_OUR_GOAL
        message["set_motor_speeds"]["left"] = 0
        message["set_motor_speeds"]["right"] = 0

    elif robot.state == RobotState.DEF_IDLE:
        if robot.distance_to_ball <= 0.3:
            robot.state = RobotState.DEF_TO_BALL
        message["set_motor_speeds"]["left"] = 0
        message["set_motor_speeds"]["right"] = 0

    elif robot.state == RobotState.DEF_INTERCEPT:
        bearing_diff = abs(robot.bearing_to_our_goal -
                           robot.bearing_to_ball) % 360 - 180
        if bearing_diff > -10 or bearing_diff < 10:
            robot.state = RobotState.DEF_TO_BALL
        intercept_ball(robot, message)


def return_to_goal(robot: Robot, message):
    print("OUR_GOAL")
    if (robot.bearing_to_our_goal < 180-15) and (robot.bearing_to_our_goal >= 90):
        turn_backleft(robot, message, (180 - robot.bearing_to_our_goal) / 180)
    elif (robot.bearing_to_our_goal > -180+15) and (robot.bearing_to_our_goal <= -90):
        turn_backright(robot, message, (180 + robot.bearing_to_our_goal) / 180)
    elif (robot.bearing_to_our_goal > 15) and (robot.bearing_to_our_goal < 90):
        turn_right(robot, message, robot.bearing_to_our_goal / 180)
    elif (robot.bearing_to_our_goal < -15) and (robot.bearing_to_our_goal > -90):
        turn_left(robot, message, -robot.bearing_to_our_goal / 180)
    elif (robot.bearing_to_our_goal <= 15) and (robot.bearing_to_our_goal >= -15):
        go_forward(robot, message)
    else:
        go_backward(robot, message)


def go_to_ball(robot: Robot, message):
    message["set_leds_colour"] = "yellow"
    if abs(robot.bearing_to_ball) < 20:
        go_forward(robot, message)
    elif robot.bearing_to_ball > 0:
        turn_right(robot, message, robot.bearing_to_ball / 180)
    else:
        turn_left(robot, message, -robot.bearing_to_ball / 180)


def face_forward(robot: Robot, message):
    print("FORWARDS")
    if robot.bearing_to_their_goal < -15:
        turn_left(robot, message, -robot.bearing_to_ball / 180)
    elif robot.bearing_to_their_goal > 15:
        turn_right(robot, message, robot.bearing_to_ball / 180)
    else:
        robot.state = RobotState.DEF_IDLE

def intercept_mid_field(robot: Robot, message):
    target_bearing = robot.bearing_to_ball
    for key, value in robot.neighbours.items():
        if value["team"] != robot.team and value["role"] == "MID_FIELD":
            target_bearing = (robot.bearing_to_ball + value["bearing"]) / 2
            if abs(robot.bearing_to_ball - value["bearing"]) > 180:
                target_bearing = angles.normalize(target_bearing+180, -180, 180)
            print("hello friend", key, value)
            print(target_bearing)

    if abs(target_bearing) < 20:
        go_forward(robot, message)
    elif target_bearing > 0:
        turn_right(robot, message, target_bearing / 180)
    else:
        turn_left(robot, message, -target_bearing / 180)


def intercept_ball(robot: Robot, message):
    target_bearing = (robot.bearing_to_ball + robot.bearing_to_our_goal) / 2
    if abs(robot.bearing_to_ball - robot.bearing_to_our_goal) > 180:
        target_bearing = angles.normalize(target_bearing+180, -180, 180)
    if abs(target_bearing) < 20:
        go_forward(robot, message)
    elif target_bearing > 0:
        turn_right(robot, message, target_bearing / 180)
    else:
        turn_left(robot, message, -target_bearing / 180)


def turn_right(robot: Robot, message, magnitude):
    ratio = 1.4 * magnitude + 2 * (1-magnitude)
    message["set_motor_speeds"]["left"] = int(float(robot.MAX_SPEED) / ratio)
    message["set_motor_speeds"]["right"] = -int(float(robot.MAX_SPEED) / ratio)


def turn_left(robot: Robot, message, magnitude):
    ratio = 1.4 * magnitude + 2 * (1-magnitude)
    message["set_motor_speeds"]["left"] = -int(float(robot.MAX_SPEED) / ratio)
    message["set_motor_speeds"]["right"] = int(float(robot.MAX_SPEED) / ratio)


def go_forward(robot: Robot, message):
    message["set_motor_speeds"]["left"] = robot.MAX_SPEED
    message["set_motor_speeds"]["right"] = robot.MAX_SPEED


def turn_backleft(robot: Robot, message, magnitude):
    turn_left(robot, message, magnitude)


def turn_backright(robot: Robot, message, magnitude):
    turn_right(robot, message, magnitude)


def go_backward(robot: Robot, message):
    message["set_motor_speeds"]["left"] = (-1)*robot.MAX_SPEED
    message["set_motor_speeds"]["right"] = (-1)*robot.MAX_SPEED


# Main entry point for robot control client sample code
if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    loop.run_until_complete(connect_to_server())

    if server_connection is None:
        print(Fore.RED + "[ERROR]: No connection to server")
        sys.exit(1)

    assert len(robot_ids) > 0

    # Create Robot objects
    for robot_id in robot_ids:
        if robots[robot_id] != '':
            active_robots[robot_id] = Robot(robot_id)
        else:
            print(f"No IP defined for robot {robot_id}")

    # Create websockets connections to robots
    print(Fore.GREEN + "[INFO]: Connecting to robots")
    loop.run_until_complete(connect_to_robots())

    if not active_robots:
        print(Fore.RED + "[ERROR]: No connection to robots")
        sys.exit(1)

    # Only communicate with robots that were successfully connected to
    while True:
        main_loop()

        if kill_now():
            # Kill all robots, even if not visible
            loop.run_until_complete(stop_robots(robot_ids))
            break
