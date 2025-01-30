import pygame
import pymunk
import pymunk.pygame_util
import random
import math
from collections import deque

# Simulation Constants and Parameters
WIDTH, HEIGHT = 1280, 720
FPS = 60
NUM_PARTICLES = 100
MIN_RADIUS, MAX_RADIUS = 5, 50
INITIAL_VELOCITY_RANGE = (-200, 200)
INITIAL_ANGULAR_VELOCITY_RANGE = (-5, 5)
FRICTION_COEFFICIENT = 0.5
GRAVITY_ACCELERATION = 981
ELASTICITY = 1.0
INITIAL_TIME_STEP = 1 / 60.0
MAX_HISTORY_LENGTH = 20000
FONT_SIZE = 14
FONT_NAME = "Arial"
UI_PADDING = 10
UI_WIDTH, UI_HEIGHT = 180, 180  # Restored original UI size
UI_OPACITY = 180
BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (220, 220, 220)
TEXT_HIGHLIGHT = (100, 180, 255)
UI_BACKGROUND = (20, 20, 20, UI_OPACITY)
STATUS_ON = (100, 255, 100)
STATUS_OFF = (180, 180, 180)

# Energy graph settings
GRAPH_WIDTH, GRAPH_HEIGHT = 300, 100
GRAPH_POSITION = (WIDTH - GRAPH_WIDTH - UI_PADDING, UI_PADDING)
GRAPH_COLOR = (100, 180, 255)
GRAPH_BACKGROUND = (20, 20, 20, 150)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)

# Pymunk space
space = pymunk.Space()
space.gravity = (0, 0)
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Create boundaries
def create_boundaries(space, width, height):
    rects = [
        [(width / 2, height - 10), (width, 20)],  # Top
        [(width / 2, 10), (width, 20)],          # Bottom
        [(10, height / 2), (20, height)],        # Left
        [(width - 10, height / 2), (20, height)] # Right
    ]
    for pos, size in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos
        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = ELASTICITY
        shape.friction = FRICTION_COEFFICIENT
        space.add(body, shape)

# Create a disk with random properties
def create_disk(space, friction=0.0):
    radius = random.randint(MIN_RADIUS, MAX_RADIUS)
    mass = math.pi * radius**2
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = (random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
    body.velocity = (random.uniform(*INITIAL_VELOCITY_RANGE), random.uniform(*INITIAL_VELOCITY_RANGE))
    body.angular_velocity = random.uniform(*INITIAL_ANGULAR_VELOCITY_RANGE)
    shape = pymunk.Circle(body, radius)
    shape.elasticity = ELASTICITY
    shape.friction = friction
    space.add(body, shape)
    return body

# Calculate kinetic energy
def calculate_kinetic_energy(body):
    linear_energy = 0.5 * body.mass * body.velocity.length**2
    angular_energy = 0.5 * body.moment * body.angular_velocity**2
    return linear_energy + angular_energy

# Map kinetic energy to a color
def energy_to_color(energy, average_energy):
    normalized_energy = energy / average_energy if average_energy != 0 else 0
    if normalized_energy < 1:
        red = int(255 * normalized_energy)
        green = int(255 * normalized_energy)
        blue = 255
    else:
        red = 255
        green = int(255 * (2 - normalized_energy))
        blue = int(255 * (2 - normalized_energy))
    return (max(0, min(255, red)), max(0, min(255, green)), max(0, min(255, blue)))

# Draw text with optional background
def draw_text(text, pos, color=TEXT_COLOR, background=None):
    text_surface = font.render(text, True, color)
    if background:
        padding = 3
        bg_rect = pygame.Rect(pos[0] - padding, pos[1] - padding,
                              text_surface.get_width() + 2 * padding,
                              text_surface.get_height() + 2 * padding)
        pygame.draw.rect(screen, background, bg_rect, border_radius=2)
    screen.blit(text_surface, pos)

# Save and load simulation state
def save_state():
    return [(body.position, body.velocity, body.angle, body.angular_velocity) for body in space.bodies]

def load_state(state):
    for body, (position, velocity, angle, angular_velocity) in zip(space.bodies, state):
        body.position = position
        body.velocity = velocity
        body.angle = angle
        body.angular_velocity = angular_velocity

# Initialize simulation
create_boundaries(space, WIDTH, HEIGHT)
disks = [create_disk(space) for _ in range(NUM_PARTICLES)]
initial_energies = [calculate_kinetic_energy(body) for body in disks]
average_energy = sum(initial_energies) / len(initial_energies) if initial_energies else 0

# Simulation control variables
running = True
simulation_paused = False
friction_enabled = False
gravity_enabled = False
invert_simulation = False
dt = INITIAL_TIME_STEP
history = deque(maxlen=MAX_HISTORY_LENGTH)

# Energy graph data
energy_history = deque(maxlen=GRAPH_WIDTH)

# Main loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                simulation_paused = not simulation_paused
            elif event.key == pygame.K_r:
                space = pymunk.Space()
                space.gravity = (0, 0) if not gravity_enabled else (0, GRAVITY_ACCELERATION)
                create_boundaries(space, WIDTH, HEIGHT)
                disks = [create_disk(space, friction=0.1 if friction_enabled else 0) for _ in range(NUM_PARTICLES)]
                initial_energies = [calculate_kinetic_energy(body) for body in disks]
                average_energy = sum(initial_energies) / len(initial_energies)
                history.clear()
                energy_history.clear()
            elif event.key == pygame.K_f:
                friction_enabled = not friction_enabled
                for body in space.bodies:
                    for shape in body.shapes:
                        if isinstance(shape, pymunk.Circle):
                            shape.friction = 0.1 if friction_enabled else 0
            elif event.key == pygame.K_g:
                gravity_enabled = not gravity_enabled
                space.gravity = (0, GRAVITY_ACCELERATION) if gravity_enabled else (0, 0)
            elif event.key == pygame.K_i:
                invert_simulation = not invert_simulation
            elif event.key == pygame.K_UP:
                dt *= 1.1
            elif event.key == pygame.K_DOWN:
                dt *= 0.9
        elif event.type == pygame.MOUSEBUTTONDOWN:
            new_disk = create_disk(space, friction=0.1 if friction_enabled else 0)
            disks.append(new_disk)
            initial_energies.append(calculate_kinetic_energy(new_disk))
            average_energy = sum(initial_energies) / len(initial_energies)

    # Clear screen
    screen.fill(BACKGROUND_COLOR)

    # Draw particles
    for body in space.bodies:
        for shape in body.shapes:
            if isinstance(shape, pymunk.Circle):
                energy = calculate_kinetic_energy(body)
                color = energy_to_color(energy, average_energy)
                radius = shape.radius
                position = body.position
                pygame.draw.circle(screen, color, (int(position.x), int(position.y)), int(radius))
                angle = body.angle
                end_x = position.x + math.cos(angle) * radius
                end_y = position.y + math.sin(angle) * radius
                pygame.draw.line(screen, (255, 255, 255), (int(position.x), int(position.y)), (int(end_x), int(end_y)), 2)

    # Calculate total energy
    total_energy = sum(calculate_kinetic_energy(body) for body in space.bodies)
    energy_history.append(total_energy)

    # Draw energy graph
    graph_surface = pygame.Surface((GRAPH_WIDTH, GRAPH_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(graph_surface, GRAPH_BACKGROUND, graph_surface.get_rect(), border_radius=3)
    if len(energy_history) > 1:
        max_energy = max(energy_history) if max(energy_history) != 0 else 1  # Avoid division by zero
        points = []
        for i, energy in enumerate(energy_history):
            if not math.isnan(energy):  # Skip NaN values
                x = int((i / GRAPH_WIDTH) * GRAPH_WIDTH)
                y = int((1 - energy / max_energy) * GRAPH_HEIGHT)
                points.append((x, y))
        if points:  # Only draw if there are valid points
            pygame.draw.lines(graph_surface, GRAPH_COLOR, False, points, 2)
    screen.blit(graph_surface, GRAPH_POSITION)

    # Draw UI panel
    ui_panel = pygame.Surface((UI_WIDTH, UI_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(ui_panel, UI_BACKGROUND, ui_panel.get_rect(), border_radius=3)
    screen.blit(ui_panel, (UI_PADDING, UI_PADDING))

    # Draw UI text
    y_offset = UI_PADDING + 5
    controls = [
        (f"Simulation: {'PAUSED' if simulation_paused else 'RUNNING'}", STATUS_ON if not simulation_paused else STATUS_OFF),
        ("Controls:", TEXT_HIGHLIGHT),
        ("SPACE - Pause/Resume", None),
        ("R - Reset", None),
        (f"F - Friction [{('ON' if friction_enabled else 'OFF')}]", STATUS_ON if friction_enabled else STATUS_OFF),
        (f"G - Gravity [{('ON' if gravity_enabled else 'OFF')}]", STATUS_ON if gravity_enabled else STATUS_OFF),
        (f"I - Inversion [{('ON' if invert_simulation else 'OFF')}]", STATUS_ON if invert_simulation else STATUS_OFF),
        ("↑/↓ - Time Step", None),
        (f"dt: {dt:.6f}", TEXT_HIGHLIGHT),
    ]
    for text, color in controls:
        draw_text(text, (UI_PADDING + 5, y_offset), color=color or TEXT_COLOR)
        y_offset += FONT_SIZE + 4

    # Update physics
    if not simulation_paused:
        if invert_simulation:
            if len(history) > 1:
                load_state(history.pop())
        else:
            history.append(save_state())
            space.step(dt)

    # Update display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()