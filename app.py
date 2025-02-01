import pygame
import pymunk
import pymunk.pygame_util
import random
import math
from collections import deque

# Screen and simulation parameters
WIDTH = 720
HEIGHT = 720
FPS = 60

# Particle settings
NUM_PARTICLES = 400  # Fewer particles for improved performance
PARTICLE_RADIUS_RANGE = (5, 20)
INITIAL_VELOCITY_RANGE = (-200, 200)
INITIAL_ANGULAR_VELOCITY_RANGE = (-15, 15)

# Physics parameters
DEFAULT_FRICTION = 0.1      # Nonzero friction enables transfer of angular momentum
GRAVITY_ACCELERATION = 981  # pixels/s²
ELASTICITY = 1.0
INITIAL_TIME_STEP = 1 / 60.0

# History settings for inversion (set to a positive value)
MAX_HISTORY_LENGTH = 1000

# UI settings and colors
FONT_SIZE = 14
FONT_NAME = "Arial"
UI_PADDING = 10
UI_WIDTH = 180
UI_HEIGHT = 180
UI_OPACITY = 180

BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (220, 220, 220)
TEXT_HIGHLIGHT = (100, 180, 255)
UI_BACKGROUND = (20, 20, 20, UI_OPACITY)
STATUS_ON = (100, 255, 100)
STATUS_OFF = (180, 180, 180)

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Improved Particle Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        
        # Initialize the physics space.
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        
        # Simulation control variables.
        self.running = True
        self.paused = False
        self.friction_enabled = False  # Off by default; toggle with 'F'
        self.gravity_enabled = False   # Off by default; toggle with 'G'
        self.inversion_enabled = False # Off by default; toggle with 'I'
        self.dt = INITIAL_TIME_STEP
        
        # History: only dynamic particle states are stored.
        self.history = deque(maxlen=MAX_HISTORY_LENGTH)
        
        # Keep track of dynamic particles (disks) separately.
        self.particles = []
        
        # Set up boundaries and particles.
        self.create_boundaries()
        self.create_particles(NUM_PARTICLES)
        
        # Compute the initial average kinetic energy.
        self.initial_energies = [self.calculate_kinetic_energy(p.body) for p in self.particles]
        self.average_energy = (sum(self.initial_energies) / len(self.initial_energies)
                               if self.initial_energies else 0)
    
    def create_boundaries(self):
        """Create four static walls that form a box around the simulation area."""
        boundary_defs = [
            ((WIDTH / 2, HEIGHT - 10), (WIDTH, 20)),   # Top
            ((WIDTH / 2, 10), (WIDTH, 20)),              # Bottom
            ((10, HEIGHT / 2), (20, HEIGHT)),            # Left
            ((WIDTH - 10, HEIGHT / 2), (20, HEIGHT))       # Right
        ]
        for pos, size in boundary_defs:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = pos
            shape = pymunk.Poly.create_box(body, size)
            shape.elasticity = ELASTICITY
            shape.friction = DEFAULT_FRICTION
            self.space.add(body, shape)
    
    class Particle:
        def __init__(self, space, friction=0.0):
            # Randomize the radius, mass (proportional to area), and moment of inertia.
            self.radius = random.randint(PARTICLE_RADIUS_RANGE[0], PARTICLE_RADIUS_RANGE[1])
            self.mass = math.pi * self.radius ** 2
            self.moment = pymunk.moment_for_circle(self.mass, 0, self.radius)
            self.body = pymunk.Body(self.mass, self.moment)
            # Spawn particles away from the very edge.
            self.body.position = (random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
            self.body.velocity = (
                random.uniform(INITIAL_VELOCITY_RANGE[0], INITIAL_VELOCITY_RANGE[1]),
                random.uniform(INITIAL_VELOCITY_RANGE[0], INITIAL_VELOCITY_RANGE[1])
            )
            self.body.angular_velocity = random.uniform(INITIAL_ANGULAR_VELOCITY_RANGE[0],
                                                        INITIAL_ANGULAR_VELOCITY_RANGE[1])
            self.shape = pymunk.Circle(self.body, self.radius)
            self.shape.elasticity = ELASTICITY
            self.shape.friction = friction
            space.add(self.body, self.shape)
    
    def create_particles(self, count):
        """Instantiate a given number of particles."""
        self.particles = []
        for _ in range(count):
            particle = self.Particle(self.space, friction=DEFAULT_FRICTION if self.friction_enabled else 0)
            self.particles.append(particle)
    
    def calculate_kinetic_energy(self, body):
        """Return the sum of translational and rotational kinetic energy."""
        linear_energy = 0.5 * body.mass * (body.velocity.length ** 2)
        angular_energy = 0.5 * body.moment * (body.angular_velocity ** 2)
        return linear_energy + angular_energy
    
    def energy_to_color(self, energy):
        """
        Map kinetic energy to an RGB color.
        Below average: blue-to-white gradient.
        Above average: white-to-red gradient.
        """
        avg = self.average_energy if self.average_energy > 0 else 1
        if energy < avg:
            norm = energy / avg
            red = int(255 * norm)
            green = int(255 * norm)
            blue = 255
        else:
            norm = (energy - avg) / avg
            red = 255
            green = int(255 * (1 - norm))
            blue = int(255 * (1 - norm))
        return (max(0, min(255, red)),
                max(0, min(255, green)),
                max(0, min(255, blue)))
    
    def save_state(self):
        """
        Save the current state (position, velocity, angle, angular_velocity)
        for each particle.
        """
        state = []
        for p in self.particles:
            b = p.body
            state.append((b.position, b.velocity, b.angle, b.angular_velocity))
        return state
    
    def load_state(self, state):
        """Load a saved state into the corresponding particles."""
        for particle, s in zip(self.particles, state):
            b = particle.body
            pos, vel, angle, ang_vel = s
            b.position = pos
            b.velocity = vel
            b.angle = angle
            b.angular_velocity = ang_vel
    
    def count_particles(self):
        """Count how many particles are currently within the screen bounds."""
        count = 0
        for p in self.particles:
            x, y = p.body.position
            if 0 < x < WIDTH and 0 < y < HEIGHT:
                count += 1
        return count
    
    def draw_text(self, text, pos, color=TEXT_COLOR, background=None):
        """Helper function to render text onto the screen."""
        text_surface = self.font.render(text, True, color)
        if background:
            padding = 3
            bg_rect = pygame.Rect(pos[0] - padding, pos[1] - padding,
                                  text_surface.get_width() + 2 * padding,
                                  text_surface.get_height() + 2 * padding)
            pygame.draw.rect(self.screen, background, bg_rect, border_radius=2)
        self.screen.blit(text_surface, pos)
    
    def handle_events(self):
        """Process all incoming events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset_simulation()
                elif event.key == pygame.K_f:
                    self.friction_enabled = not self.friction_enabled
                    # Update friction on all particles.
                    for p in self.particles:
                        p.shape.friction = DEFAULT_FRICTION if self.friction_enabled else 0
                elif event.key == pygame.K_g:
                    self.gravity_enabled = not self.gravity_enabled
                    self.space.gravity = (0, GRAVITY_ACCELERATION) if self.gravity_enabled else (0, 0)
                elif event.key == pygame.K_i:
                    self.inversion_enabled = not self.inversion_enabled
                    # When turning off inversion, clear history to avoid a freeze.
                    if not self.inversion_enabled:
                        self.history.clear()
                elif event.key == pygame.K_UP:
                    self.dt *= 1.1
                elif event.key == pygame.K_DOWN:
                    self.dt *= 0.9
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    # Add a new particle.
                    new_particle = self.Particle(self.space, friction=DEFAULT_FRICTION if self.friction_enabled else 0)
                    self.particles.append(new_particle)
                    self.initial_energies.append(self.calculate_kinetic_energy(new_particle.body))
                    self.average_energy = sum(self.initial_energies) / len(self.initial_energies)
                elif event.key == pygame.K_MINUS:
                    # Remove a particle if any exist.
                    if self.particles:
                        removed = self.particles.pop()
                        self.space.remove(removed.body, removed.shape)
                        if self.initial_energies:
                            self.initial_energies.pop()
                        if self.initial_energies:
                            self.average_energy = sum(self.initial_energies) / len(self.initial_energies)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Add a particle on mouse click.
                new_particle = self.Particle(self.space, friction=DEFAULT_FRICTION if self.friction_enabled else 0)
                self.particles.append(new_particle)
                self.initial_energies.append(self.calculate_kinetic_energy(new_particle.body))
                self.average_energy = sum(self.initial_energies) / len(self.initial_energies)
    
    def reset_simulation(self):
        """Reset the simulation: clear history, rebuild space, boundaries, and particles."""
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY_ACCELERATION) if self.gravity_enabled else (0, 0)
        self.history.clear()
        self.particles.clear()
        self.create_boundaries()
        self.create_particles(NUM_PARTICLES)
        self.initial_energies = [self.calculate_kinetic_energy(p.body) for p in self.particles]
        self.average_energy = (sum(self.initial_energies) / len(self.initial_energies)
                               if self.initial_energies else 0)
    
    def update(self):
        """Update the simulation physics or, if inversion is enabled, restore an earlier state."""
        if not self.paused:
            if self.inversion_enabled:
                # If there is a saved state, load the last one.
                if len(self.history) > 0:
                    state = self.history.pop()
                    self.load_state(state)
            else:
                # Save the current state, then step the simulation forward.
                self.history.append(self.save_state())
                self.space.step(self.dt)
    
    def draw(self):
        """Render the simulation and UI."""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw each particle with a color based on its kinetic energy.
        for p in self.particles:
            pos = p.body.position
            energy = self.calculate_kinetic_energy(p.body)
            color = self.energy_to_color(energy)
            pygame.draw.circle(self.screen, color, (int(pos.x), int(pos.y)), int(p.radius))
            # Draw a line indicating the particle's orientation.
            angle = p.body.angle
            end_x = pos.x + math.cos(angle) * p.radius
            end_y = pos.y + math.sin(angle) * p.radius
            pygame.draw.line(self.screen, (255, 255, 255),
                             (int(pos.x), int(pos.y)), (int(end_x), int(end_y)), 2)
        
        # Draw the UI panel.
        ui_panel = pygame.Surface((UI_WIDTH, UI_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(ui_panel, UI_BACKGROUND, ui_panel.get_rect(), border_radius=3)
        self.screen.blit(ui_panel, (UI_PADDING, UI_PADDING))
        
        y_offset = UI_PADDING + 5
        controls = [
            (f"Simulation: {'PAUSED' if self.paused else 'RUNNING'}",
             STATUS_OFF if self.paused else STATUS_ON),
            ("Controls:", TEXT_HIGHLIGHT),
            ("SPACE - Pause/Resume", None),
            ("R - Reset", None),
            (f"F - Friction [{'ON' if self.friction_enabled else 'OFF'}]",
             STATUS_ON if self.friction_enabled else STATUS_OFF),
            (f"G - Gravity [{'ON' if self.gravity_enabled else 'OFF'}]",
             STATUS_ON if self.gravity_enabled else STATUS_OFF),
            (f"I - Inversion [{'ON' if self.inversion_enabled else 'OFF'}]",
             STATUS_ON if self.inversion_enabled else STATUS_OFF),
            ("↑/↓ - Time Step", None),
            (f"dt: {self.dt:.6f}", TEXT_HIGHLIGHT),
            (f"Particles: {self.count_particles()}", TEXT_HIGHLIGHT),
            ("+/- - Add/Remove", None),
        ]
        
        for text, color in controls:
            self.draw_text(text, (UI_PADDING + 5, y_offset), color=color if color else TEXT_COLOR)
            y_offset += FONT_SIZE + 4
        
        pygame.display.flip()
    
    def run(self):
        """Main loop of the simulation."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()
