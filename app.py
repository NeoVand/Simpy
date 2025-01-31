import pygame
import pymunk
import pymunk.pygame_util
import random
import math
from collections import deque

# Simulation Constants and Parameters
# Screen settings
WIDTH = 1280
HEIGHT = 720
FPS = 60

# Particle settings
NUM_PARTICLES = 1000
PARTICLE_RADIUS_RANGE = (1, 5)
INITIAL_VELOCITY_RANGE = (-200, 200)
INITIAL_ANGULAR_VELOCITY_RANGE = (-5, 5)

# Physics parameters
FRICTION_COEFFICIENT = 0.5
GRAVITY_ACCELERATION = 981  # pixels/s² (≈ 9.81 m/s²)
ELASTICITY = 1.0  # 1.0 = perfectly elastic collisions
INITIAL_TIME_STEP = 1/60.0

# History settings
MAX_HISTORY_LENGTH = 20000

# UI settings
FONT_SIZE = 14
FONT_NAME = "Arial"
UI_PADDING = 10
UI_WIDTH = 180
UI_HEIGHT = 180
UI_OPACITY = 180  # 0-255

# UI Colors
BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (220, 220, 220)
TEXT_HIGHLIGHT = (100, 180, 255)
UI_BACKGROUND = (20, 20, 20, UI_OPACITY)
STATUS_ON = (100, 255, 100)
STATUS_OFF = (180, 180, 180)

# Initialize Pygame
pygame.init()

# Screen dimensions
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Pymunk space
space = pymunk.Space()
space.gravity = (0, 0)  # Start with no gravity

# Draw options for debugging
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Create a static box boundary
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
        shape.friction = FRICTION_COEFFICIENT  # Add friction to walls
        space.add(body, shape)

# Create a disk with random size, mass, and angular velocity
def create_disk(space, friction=0.0):
    radius = random.randint(PARTICLE_RADIUS_RANGE[0], PARTICLE_RADIUS_RANGE[1])
    mass = math.pi * radius**2
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = (random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
    body.velocity = (
        random.uniform(INITIAL_VELOCITY_RANGE[0], INITIAL_VELOCITY_RANGE[1]), 
        random.uniform(INITIAL_VELOCITY_RANGE[0], INITIAL_VELOCITY_RANGE[1])
    )
    body.angular_velocity = random.uniform(
        INITIAL_ANGULAR_VELOCITY_RANGE[0], 
        INITIAL_ANGULAR_VELOCITY_RANGE[1]
    )
    shape = pymunk.Circle(body, radius)
    shape.elasticity = ELASTICITY
    shape.friction = friction
    space.add(body, shape)
    return body

# Create boundaries
create_boundaries(space, WIDTH, HEIGHT)

# Create disks and calculate initial average kinetic energy
disks = [create_disk(space) for _ in range(NUM_PARTICLES)]

# Function to calculate kinetic energy
def calculate_kinetic_energy(body):
    linear_energy = 0.5 * body.mass * body.velocity.length**2
    angular_energy = 0.5 * body.moment * body.angular_velocity**2
    return linear_energy + angular_energy

# Calculate initial average kinetic energy
initial_energies = [calculate_kinetic_energy(body) for body in disks]
average_energy = sum(initial_energies) / len(initial_energies)

# Function to map kinetic energy to a color (blue to red gradient)
def energy_to_color(energy, average_energy):
    # Normalize energy relative to average
    if energy < average_energy:
        # Below average: interpolate between blue and white
        normalized_energy = energy / average_energy
        red = int(255 * normalized_energy)
        green = int(255 * normalized_energy)
        blue = 255
    else:
        # Above average: interpolate between white and red
        normalized_energy = (energy - average_energy) / average_energy
        red = 255
        green = int(255 * (1 - normalized_energy))
        blue = int(255 * (1 - normalized_energy))
    # Clamp color values to [0, 255]
    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))
    return (red, green, blue)

# Simulation control variables
running = True
simulation_paused = False
friction_enabled = False  # Friction off by default
gravity_enabled = False   # Gravity toggle
invert_simulation = False # Inversion toggle
dt = 1 / 60.0            # Initial time step
history = deque(maxlen=MAX_HISTORY_LENGTH)  # Store simulation states for inversion

# UI elements
font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
def draw_text(text, pos, color=TEXT_COLOR, background=None):
    text_surface = font.render(text, True, color)
    if background:
        padding = 3  # Reduced padding
        bg_rect = pygame.Rect(pos[0]-padding, pos[1]-padding, 
                            text_surface.get_width()+2*padding, 
                            text_surface.get_height()+2*padding)
        pygame.draw.rect(screen, background, bg_rect, border_radius=2)
    screen.blit(text_surface, pos)

# Function to save the current state of the simulation
def save_state():
    state = []
    for body in space.bodies:
        state.append((body.position, body.velocity, body.angle, body.angular_velocity))
    return state

# Function to load a saved state into the simulation
def load_state(state):
    for body, (position, velocity, angle, angular_velocity) in zip(space.bodies, state):
        body.position = position
        body.velocity = velocity
        body.angle = angle
        body.angular_velocity = angular_velocity

# Main loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                simulation_paused = not simulation_paused
            elif event.key == pygame.K_r:
                # Reset simulation
                space = pymunk.Space()
                space.gravity = (0, 0) if not gravity_enabled else (0, 981)
                create_boundaries(space, WIDTH, HEIGHT)
                disks = [create_disk(space, friction=0.1 if friction_enabled else 0) for _ in range(NUM_PARTICLES)]
                initial_energies = [calculate_kinetic_energy(body) for body in disks]
                average_energy = sum(initial_energies) / len(initial_energies)
                history.clear()  # Clear history on reset
            elif event.key == pygame.K_f:
                # Toggle friction
                friction_enabled = not friction_enabled
                for body in space.bodies:
                    for shape in body.shapes:
                        if isinstance(shape, pymunk.Circle):
                            shape.friction = 0.1 if friction_enabled else 0
            elif event.key == pygame.K_g:
                # Toggle gravity
                gravity_enabled = not gravity_enabled
                space.gravity = (0, 981) if gravity_enabled else (0, 0)
            elif event.key == pygame.K_i:
                # Toggle inversion
                invert_simulation = not invert_simulation
            elif event.key == pygame.K_UP:
                # Increase time step
                dt *= 1.1
            elif event.key == pygame.K_DOWN:
                # Decrease time step
                dt *= 0.9
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Add a new disk on mouse click
            new_disk = create_disk(space, friction=0.1 if friction_enabled else 0)
            disks.append(new_disk)
            initial_energies.append(calculate_kinetic_energy(new_disk))
            average_energy = sum(initial_energies) / len(initial_energies)

    # Clear screen
    screen.fill((0, 0, 0))

    # Draw disks with energy-based colors and rotation indicator
    for body in space.bodies:
        for shape in body.shapes:
            if isinstance(shape, pymunk.Circle):
                energy = calculate_kinetic_energy(body)
                color = energy_to_color(energy, average_energy)
                radius = shape.radius
                position = body.position
                # Draw the disk
                pygame.draw.circle(screen, color, (int(position.x), int(position.y)), int(radius))
                # Draw a line to indicate rotation
                angle = body.angle
                end_x = position.x + math.cos(angle) * radius
                end_y = position.y + math.sin(angle) * radius
                pygame.draw.line(screen, (255, 255, 255), (int(position.x), int(position.y)), (int(end_x), int(end_y)), 2)

    # Draw UI panel
    ui_panel = pygame.Surface((UI_WIDTH, UI_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(ui_panel, UI_BACKGROUND, ui_panel.get_rect(), border_radius=3)
    screen.blit(ui_panel, (UI_PADDING, UI_PADDING))

    # Draw UI text with better formatting
    y_offset = UI_PADDING + 5
    controls = [
        (f"Simulation: {'PAUSED' if simulation_paused else 'RUNNING'}", 
         STATUS_ON if not simulation_paused else STATUS_OFF),
        ("Controls:", TEXT_HIGHLIGHT),
        ("SPACE - Pause/Resume", None),
        ("R - Reset", None),
        (f"F - Friction [{('ON' if friction_enabled else 'OFF')}]",
         STATUS_ON if friction_enabled else STATUS_OFF),
        (f"G - Gravity [{('ON' if gravity_enabled else 'OFF')}]",
         STATUS_ON if gravity_enabled else STATUS_OFF),
        (f"I - Inversion [{('ON' if invert_simulation else 'OFF')}]",
         STATUS_ON if invert_simulation else STATUS_OFF),
        ("↑/↓ - Time Step", None),
        (f"dt: {dt:.6f}", TEXT_HIGHLIGHT),
    ]

    for text, color in controls:
        draw_text(text, (UI_PADDING + 5, y_offset), 
                 color=color or TEXT_COLOR)
        y_offset += FONT_SIZE + 4  # Reduced spacing between lines

    # Update physics
    if not simulation_paused:
        if invert_simulation:
            # Play simulation in reverse
            if len(history) > 1:
                load_state(history.pop())  # Pop the most recent state
        else:
            # Play simulation forward
            history.append(save_state())  # Save the current state
            space.step(dt)

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
