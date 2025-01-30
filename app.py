import pygame
import pymunk
import pymunk.pygame_util
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1000, 1000
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
        shape.elasticity = 1.0  # Perfectly elastic collisions
        space.add(body, shape)

# Create a disk with random size, mass, and angular velocity
def create_disk(space, friction=0.1):
    radius = random.randint(10, 30)
    mass = math.pi * radius**2  # Mass proportional to area
    moment = pymunk.moment_for_circle(mass, 0, radius)  # Moment of inertia for a disk
    body = pymunk.Body(mass, moment)
    body.position = (random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
    body.velocity = (random.uniform(-200, 200), random.uniform(-200, 200))
    body.angular_velocity = random.uniform(-5, 5)  # Random initial angular velocity
    shape = pymunk.Circle(body, radius)
    shape.elasticity = 1.0  # Perfectly elastic collisions
    shape.friction = friction  # Friction for the disk
    space.add(body, shape)
    return body

# Create boundaries
create_boundaries(space, WIDTH, HEIGHT)

# Create disks and calculate initial average kinetic energy
disks = [create_disk(space) for _ in range(100)]

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
friction_enabled = True  # Friction toggle
gravity_enabled = False  # Gravity toggle
dt = 1 / 60.0  # Delta time for simulation

# UI elements
font = pygame.font.SysFont("Arial", 18)
def draw_text(text, pos, color=(255, 255, 255)):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, pos)

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
                space.gravity = (0, 0) if not gravity_enabled else (0, 981)  # 981 pixels/s² ≈ 9.81 m/s²
                create_boundaries(space, WIDTH, HEIGHT)
                disks = [create_disk(space, friction=0.1 if friction_enabled else 0) for _ in range(100)]
                initial_energies = [calculate_kinetic_energy(body) for body in disks]
                average_energy = sum(initial_energies) / len(initial_energies)
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
                space.gravity = (0, 981) if gravity_enabled else (0, 0)  # 981 pixels/s² ≈ 9.81 m/s²
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

    # Draw UI
    draw_text(f"Simulation {'Paused' if simulation_paused else 'Running'}", (10, 10))
    draw_text("Press SPACE to pause/resume", (10, 30))
    draw_text("Press R to reset", (10, 50))
    draw_text("Press F to toggle friction", (10, 70))
    draw_text("Press G to toggle gravity", (10, 90))
    draw_text("Click to add a disk", (10, 110))
    draw_text(f"Friction: {'ON' if friction_enabled else 'OFF'}", (10, 130))
    draw_text(f"Gravity: {'ON' if gravity_enabled else 'OFF'}", (10, 150))

    # Update physics
    if not simulation_paused:
        space.step(dt)

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()