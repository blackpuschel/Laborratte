from math import sqrt
import pygame

pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
MAX_FPS = 20
frame_counter = 0

nodes = [
    (0, 500),
    (1000, 500),
    (1000, 300),
    (1200, 300),
]


def drawNodes():
    pygame.draw.circle(screen, "green", nodes[0], 16, 4)
    shift = frame_counter % MAX_FPS * 1.9
    for i in range(1, len(nodes)):
        pygame.draw.circle(screen, "green", nodes[i], 16, 4)
        drawDashedLine(screen, "green", nodes[i-1], nodes[i], 1, 20, 1, 16, shift)

def drawDashedLine(surface, color, start_pos, end_pos, width=1, size=1, spacing=1, margin=0, shift=0):
    direction = subtract_vectors(end_pos, start_pos)
    normalized_direction = normalize_vector(direction)

    marginalized_direction = scale_vector(normalized_direction, margin)
    start_pos = add_vectors(start_pos, marginalized_direction)
    end_pos = subtract_vectors(end_pos, marginalized_direction)

    shifted_direction = scale_vector(normalized_direction, shift)
    start_pos = add_vectors(start_pos, shifted_direction)

    direction = subtract_vectors(end_pos, start_pos)

    scaled_direction = scale_vector(normalized_direction, size)
    scaled_spacing = scale_vector(scaled_direction, spacing)

    total_length = vector_length(direction)
    dashes_in_line = int(total_length / (size + size * spacing))

    distance = add_vectors(scaled_direction, scaled_spacing)
    line_start = start_pos
    for i in range(0, dashes_in_line):
        line_end = add_vectors(line_start, scaled_direction)
        pygame.draw.line(surface, color, line_start, line_end, width)
        line_start = add_vectors(line_start, distance)

    pygame.draw.line(surface, color, line_start, end_pos, width)

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
    if frame_counter > MAX_FPS:
        frame_counter = 0

    drawNodes()

    pygame.display.flip()
    screen.fill("black")
    pygame.display.flip

    clock.tick(MAX_FPS) / 1000

pygame.quit()
