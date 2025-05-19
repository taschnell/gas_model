import pygame
import math
import random
import threading
import time

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 900
NUM_PARTICLES = 5000
SIMULATION_RATE = 100  # Hz
RENDER_RATE = 60       # FPS
GRID_SIZE = 10         # Grid cell size in pixels
k_B = 1.380649e-23     # Boltzmann constant in J/K
mass = 4.65e-26        # Mass of nitrogen molecule (N2) in kg
Target_Temp = 300      # Kelvin

class Particle:
    def __init__(self, mass, x, y, velocity_x, velocity_y, radius):
        self.m = mass
        self.x = x
        self.y = y
        self.v_x = velocity_x
        self.v_y = velocity_y
        self.r = radius

    def move(self, dt):
        self.x += self.v_x * dt
        self.y += self.v_y * dt

        wall_bounce = 0

        # Bounce off walls
        if self.x - self.r < 0 or self.x + self.r > SCREEN_WIDTH:
            self.v_x *= -1
            self.x = max(self.r, min(SCREEN_WIDTH - self.r, self.x))
            wall_bounce += 1
        if self.y - self.r < 0 or self.y + self.r > SCREEN_HEIGHT:
            self.v_y *= -1
            self.y = max(self.r, min(SCREEN_HEIGHT - self.r, self.y))
            wall_bounce += 1

        return wall_bounce

    def draw(self, screen, color=(255, 0, 0)):
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.r)

    def check_collision(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        dist = math.hypot(dx, dy)
        return dist < self.r + other.r

    def resolve_collision(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return  # prevent division by zero

        # Normal vector
        nx = dx / dist
        ny = dy / dist

        # Relative velocity
        dvx = self.v_x - other.v_x
        dvy = self.v_y - other.v_y

        # Dot product of relative velocity and normal
        dot = dvx * nx + dvy * ny

        if dot > 0:
            return  # Already moving away

        restitution = 1.0  # perfectly elastic

        impulse = (-(1 + restitution) * dot) / (1 / self.m + 1 / other.m)
        impulse_x = impulse * nx
        impulse_y = impulse * ny

        self.v_x += impulse_x / self.m
        self.v_y += impulse_y / self.m
        other.v_x -= impulse_x / other.m
        other.v_y -= impulse_y / other.m

        # Optional: resolve overlap
        overlap = 0.5 * (self.r + other.r - dist + 1)
        self.x -= nx * overlap
        self.y -= ny * overlap
        other.x += nx * overlap
        other.y += ny * overlap


# Shared particle list and lock
particles = []
lock = threading.Lock()
bounces = 0

def get_cell(x, y):
    return int(x // GRID_SIZE), int(y // GRID_SIZE)

def simulate():
    global bounces
    dt = 1.0 / SIMULATION_RATE
    perimeter = 2 * (SCREEN_WIDTH + SCREEN_HEIGHT)  # meters, since 1 pixel = 1 meter

    t = 0
    total_momentum_transfer = 0.0  # kg·m/s

    while True:
        with lock:
            for p in particles:
                # Before move: store velocity for momentum transfer calc
                old_vx, old_vy = p.v_x, p.v_y
                wall_bounce = p.move(dt)

                # Calculate momentum transfer only if wall collision occurred
                if wall_bounce:
                    if p.x - p.r <= 0 or p.x + p.r >= SCREEN_WIDTH:
                        total_momentum_transfer += 2 * p.m * abs(old_vx)
                    if p.y - p.r <= 0 or p.y + p.r >= SCREEN_HEIGHT:
                        total_momentum_transfer += 2 * p.m * abs(old_vy)

                bounces += wall_bounce

            # Spatial grid for particle collisions
            grid = {}
            for p in particles:
                cell = get_cell(p.x, p.y)
                grid.setdefault(cell, []).append(p)

            visited = set()
            for cell, cell_particles in grid.items():
                neighbors = [
                    (cell[0] + dx, cell[1] + dy)
                    for dx in (-1, 0, 1)
                    for dy in (-1, 0, 1)
                ]
                for a in cell_particles:
                    for neighbor in neighbors:
                        for b in grid.get(neighbor, []):
                            if a is b or (id(a), id(b)) in visited or (id(b), id(a)) in visited:
                                continue
                            if a.check_collision(b):
                                a.resolve_collision(b)
                            visited.add((id(a), id(b)))

        # Once per second
        t += 1
        if t % SIMULATION_RATE == 0:
            pressure = total_momentum_transfer / perimeter  # in Pascals (N/m)
            k_B = 1.38e-23
            Target_Temp = 300  # Kelvin
            ideal_pressure = (len(particles) * k_B * Target_Temp) / (900**2)
            percent_diff = 100 * abs(pressure - ideal_pressure) / ideal_pressure
            print(f"Bounces/sec: {bounces}, Actual Pressure: {pressure:.3e} Pa,  Ideal Pressure: {ideal_pressure:.3e}, Percent Diff: {percent_diff:.3}%")
            bounces = 0
            total_momentum_transfer = 0.0

            


        time.sleep(dt)

def get_speeds():
    while True:
        with open("speeds.csv", "w") as file:
            for p in particles:
                speed = math.sqrt(p.v_x ** 2 + p.v_y ** 2)
                file.write(f"{speed}\n")
        time.sleep(1.5)

def main():
    v_rms = math.sqrt((2 * k_B * Target_Temp) / mass)
    global particles

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Optimized Elastic Particle Collision Simulation")
    clock = pygame.time.Clock()

    # Initialize particles
    for _ in range(NUM_PARTICLES):
        while True:
            angle = random.uniform(0, 2 * math.pi)
            v_x = v_rms * math.cos(angle)
            v_y = v_rms * math.sin(angle)
            x = random.uniform(10, SCREEN_WIDTH - 10)
            y = random.uniform(10, SCREEN_HEIGHT - 10)
            radius = 1
            p = Particle(mass, x, y, v_x, v_y, radius)

            if all(not p.check_collision(other) for other in particles):
                particles.append(p)
                break

    # Start simulation thread
    sim_thread = threading.Thread(target=simulate, daemon=True)
    sim_thread.start()

    speeds_thread = threading.Thread(target=get_speeds, daemon=True)
    speeds_thread.start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((255, 255, 255))
        with lock:
            for p in particles:
                p.draw(screen, (0, 100, 255))

        pygame.display.flip()
        clock.tick(RENDER_RATE)

    pygame.quit()

if __name__ == "__main__":
    main()
