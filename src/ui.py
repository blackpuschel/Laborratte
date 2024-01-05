from math import sqrt
import struct
from threading import Thread
import time
import pygame
import socket

pygame.init()
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
MAX_FPS = 20
frame_counter = 0
IN_HOST = ''
IN_PORT = 8080

nodes = []

right_shift = 0
up_shift = 0
scale = SCREEN_WIDTH

def shift_nodes(nodes):
    global right_shift, up_shift

    lowest_x = nodes[0][0]
    lowest_y = nodes[0][1]
    for node in nodes:
        x, y = node[0], node[1]
        if x < lowest_x:
            lowest_x = x
        if y < lowest_y:
            lowest_y = y

    need_reshift = False
    new_right_shift = 0
    if lowest_x + right_shift < 0:
        new_right_shift = abs(lowest_x)
        need_reshift = True

    new_up_shift = 0
    if lowest_y + up_shift < 0:
        new_up_shift = abs(lowest_y)
        need_reshift = True

    if need_reshift:
        reshift_nodes(new_right_shift, new_up_shift)

    shifted_nodes = []
    for node in nodes:
        x, y = node[0], node[1]

        shifted_x = x + right_shift
        shifted_y = y + up_shift

        shifted_nodes.append((shifted_x, shifted_y))
    return shifted_nodes

def reshift_nodes(new_right_shift, new_up_shift):
    global nodes, right_shift, up_shift, scale

    rescaled_nodes = []
    for node in nodes:
        scaled_x, scaled_y = node[0], node[1]

        scaled_y = abs(scaled_y - SCREEN_HEIGHT)

        shifted_x = scaled_x / scale
        shifted_y = scaled_y / scale

        x = shifted_x - right_shift
        y = shifted_y - up_shift

        shifted_x = x + new_right_shift
        shifted_y = y + new_up_shift

        scaled_x = shifted_x * scale
        scaled_y = shifted_y * scale

        scaled_y = abs(scaled_y - SCREEN_HEIGHT)

        rescaled_nodes.append((scaled_x, scaled_y))

    right_shift = new_right_shift
    up_shift = new_up_shift
    nodes = rescaled_nodes

def scale_nodes(nodes):
    global scale

    largest_x = 0
    largest_y = 0
    for node in nodes:
        x, y = node[0], node[1]
        if x > largest_x:
            largest_x = x
        if y > largest_y:
            largest_y = y

    val_x = SCREEN_WIDTH / largest_x
    val_y = SCREEN_HEIGHT / largest_y
    new_scale = val_x if val_x < val_y else val_y

    if new_scale < scale:
        rescale_nodes(new_scale)

    scaled_nodes = []
    for node in nodes:
        shifted_x, shifted_y = node[0], node[1]

        scaled_x = shifted_x * scale
        scaled_y = shifted_y * scale

        scaled_y = abs(scaled_y - SCREEN_HEIGHT)

        scaled_nodes.append((scaled_x, scaled_y))
    return scaled_nodes

def rescale_nodes(new_scale):
    global nodes, scale

    scaled_nodes = []
    for node in nodes:
        scaled_x, scaled_y = node[0], node[1]

        scaled_y = abs(scaled_y - SCREEN_HEIGHT)

        shifted_x = scaled_x / scale
        shifted_y = scaled_y / scale

        scaled_x = shifted_x * new_scale
        scaled_y = shifted_y * new_scale

        scaled_y = abs(scaled_y - SCREEN_HEIGHT)

        scaled_nodes.append((scaled_x, scaled_y))

    scale = new_scale
    nodes = scaled_nodes

def add_nodes(new_nodes):
    global nodes

    shifted_nodes = shift_nodes(new_nodes)
    scaled_nodes = scale_nodes(shifted_nodes)
    nodes.extend(scaled_nodes)
    
def byte_to_nodes(bytes: bytes):
    result = []
    for i in range(0, len(bytes), 16):
        node = struct.unpack('dd', bytes[i:i+16])
        result.append(node)
    return result

def data_thread():
    global nodes

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((IN_HOST, IN_PORT))
            s.listen()
            print(f"waiting for connection on port {IN_PORT}")
            conn, addr = s.accept()
            print("connected")
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    new_nodes = byte_to_nodes(data)
                    add_nodes(new_nodes)
                    

thread = Thread(target=data_thread, daemon=True)
thread.start()
                    
CIRCLE_SIZE = 16
LINE_SPACING = 20
def drawNodes(animate):
    nodes_copy = nodes.copy()
    if len(nodes_copy) <= 0:
        return
    
    pygame.draw.circle(screen, "green", nodes_copy[0], CIRCLE_SIZE, 4)
    phase = 100
    if animate:
        phase = frame_counter / MAX_FPS * 360
    for i in range(1, len(nodes_copy)):
        pygame.draw.circle(screen, "green", nodes_copy[i], 16, 4)

        node_distance = vector_length(subtract_vectors(nodes_copy[i], nodes_copy[i - 1]))
        circles_touchin = node_distance < 2 * CIRCLE_SIZE
        circles_to_close = node_distance < 2 * CIRCLE_SIZE + LINE_SPACING

        if not circles_touchin and circles_to_close:
            pygame.draw.line(screen, "green", nodes_copy[i-1], nodes_copy[i], 1)
        elif not circles_touchin:
            drawDashedLine(screen, "green", nodes_copy[i-1], nodes_copy[i], 1, LINE_SPACING, 1, 16, phase)

def drawDashedLine(surface, color, start_pos, end_pos, width=1, size=1, spacing=1, margin=0, phase=0):
    direction = subtract_vectors(end_pos, start_pos)
    normalized_direction = normalize_vector(direction)

    marginalized_direction = scale_vector(normalized_direction, margin)
    start_pos = add_vectors(start_pos, marginalized_direction)
    end_pos = subtract_vectors(end_pos, marginalized_direction)

    phase %= 360
    phase /= 360

    direction = subtract_vectors(end_pos, start_pos)

    scaled_direction = scale_vector(normalized_direction, size)
    scaled_spacing = scale_vector(scaled_direction, spacing)

    distance = add_vectors(scaled_direction, scaled_spacing)
    line_start = add_vectors(start_pos, scale_vector(distance, phase))

    line_end = subtract_vectors(line_start, scaled_spacing)
    if not direction_changed(subtract_vectors(line_end, start_pos), direction):
        pygame.draw.line(surface, color, start_pos, line_end, width)

    while not direction_changed(subtract_vectors(end_pos, line_start), direction):
        line_end = add_vectors(line_start, scaled_direction)
        if direction_changed(subtract_vectors(end_pos, line_end), direction):
            line_end = end_pos
        pygame.draw.line(surface, color, line_start, line_end, width)
        line_start = add_vectors(line_start, distance)

def direction_changed(direction1, direction2):
    for i in range(len(direction1)):
        if direction1[i] * direction2[i] < 0:
            return True
    return False
        

def normalize_vector(vector):
    length = vector_length(vector)
    normalized_vector = ()
    for value in vector:
        normalized_vector += (value / length,)

    return normalized_vector

def scale_vector(vector, factor):
    scaled_vector = ()
    for value in vector:
        scaled_vector += (value * factor,)

    return scaled_vector

def add_vectors(vector1, vector2, *args):
    added_vector = ()
    for i in range(len(vector1)):
        total = vector1[i] + vector2[i]
        for value in args:
            total += value[i]
        added_vector += (total,)

    return added_vector

def subtract_vectors(vector1, vector2, *args):
    subtracted_vector = ()
    for i in range(len(vector1)):
        total = vector1[i] - vector2[i]
        for value in args:
            total -= value[i]
        subtracted_vector += (total,)

    return subtracted_vector

def vector_length(vector):
    sum = 0
    for value in vector:
        sum += value * value

    return sqrt(sum)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    
    frame_counter += 1
    if frame_counter >= MAX_FPS:
        frame_counter = 0

    drawNodes(True)

    pygame.display.flip()
    screen.fill("black")
    pygame.display.flip

    clock.tick(MAX_FPS) / 1000

pygame.quit()
