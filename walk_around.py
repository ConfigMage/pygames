"""
Walk Around Game for Toddlers
A cute character explores a colorful world!
Perfect for 3-year-olds learning to use a controller or arrow keys.
"""

import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init()
pygame.joystick.init()

# Screen setup - fullscreen
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Ellie's Adventure!")

# Colors
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (124, 205, 124)
SUN_YELLOW = (255, 223, 100)
WHITE = (255, 255, 255)
PINK = (255, 182, 193)
PURPLE = (200, 162, 255)
ORANGE = (255, 180, 100)

class Flower:
    """Pretty flowers that sway in the wind"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice([PINK, PURPLE, SUN_YELLOW, ORANGE, WHITE])
        self.size = random.randint(8, 15)
        self.sway_offset = random.uniform(0, 2 * math.pi)
        self.sway_speed = random.uniform(0.02, 0.05)
        self.time = 0
        self.petals = random.randint(5, 8)

    def update(self):
        self.time += 1

    def draw(self, surface, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        # Only draw if on screen
        if -50 < screen_x < SCREEN_WIDTH + 50 and -50 < screen_y < SCREEN_HEIGHT + 50:
            sway = math.sin(self.time * self.sway_speed + self.sway_offset) * 3

            # Stem
            pygame.draw.line(surface, (80, 160, 80),
                           (int(screen_x), int(screen_y)),
                           (int(screen_x + sway), int(screen_y + 20)), 3)

            # Petals
            for i in range(self.petals):
                angle = (2 * math.pi * i / self.petals) + self.time * 0.01
                petal_x = screen_x + sway + math.cos(angle) * self.size
                petal_y = screen_y + math.sin(angle) * self.size
                pygame.draw.circle(surface, self.color, (int(petal_x), int(petal_y)), self.size // 2)

            # Center
            pygame.draw.circle(surface, SUN_YELLOW, (int(screen_x + sway), int(screen_y)), self.size // 3)

class Butterfly:
    """Butterflies that flutter around"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice([PINK, PURPLE, ORANGE, (100, 200, 255)])
        self.time = random.uniform(0, 2 * math.pi)
        self.wing_speed = random.uniform(0.2, 0.4)
        self.move_angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.5, 1.5)

    def update(self):
        self.time += 1
        # Flutter around randomly
        self.move_angle += random.uniform(-0.1, 0.1)
        self.x += math.cos(self.move_angle) * self.speed
        self.y += math.sin(self.move_angle) * self.speed + math.sin(self.time * 0.05) * 0.5

    def draw(self, surface, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        if -50 < screen_x < SCREEN_WIDTH + 50 and -50 < screen_y < SCREEN_HEIGHT + 50:
            wing_flap = abs(math.sin(self.time * self.wing_speed))
            wing_size = int(8 * wing_flap) + 4

            # Wings
            pygame.draw.ellipse(surface, self.color,
                              (int(screen_x - wing_size - 2), int(screen_y - 4), wing_size, 8))
            pygame.draw.ellipse(surface, self.color,
                              (int(screen_x + 2), int(screen_y - 4), wing_size, 8))
            # Body
            pygame.draw.ellipse(surface, (50, 50, 50),
                              (int(screen_x - 2), int(screen_y - 5), 4, 10))

class Cloud:
    """Fluffy clouds drifting by"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(0.2, 0.5)
        self.size = random.uniform(0.8, 1.5)

    def update(self):
        self.x += self.speed

    def draw(self, surface, camera_x, camera_y):
        screen_x = self.x - camera_x * 0.3  # Parallax - clouds move slower
        screen_y = self.y

        # Wrap around
        if screen_x > SCREEN_WIDTH + 200:
            self.x -= SCREEN_WIDTH + 400

        if -200 < screen_x < SCREEN_WIDTH + 200:
            size = int(40 * self.size)
            pygame.draw.circle(surface, WHITE, (int(screen_x), int(screen_y)), size)
            pygame.draw.circle(surface, WHITE, (int(screen_x - size * 0.7), int(screen_y + 10)), int(size * 0.7))
            pygame.draw.circle(surface, WHITE, (int(screen_x + size * 0.7), int(screen_y + 5)), int(size * 0.8))
            pygame.draw.circle(surface, WHITE, (int(screen_x - size * 0.3), int(screen_y - size * 0.4)), int(size * 0.6))
            pygame.draw.circle(surface, WHITE, (int(screen_x + size * 0.4), int(screen_y - size * 0.3)), int(size * 0.5))

class Footprint:
    """Little footprints left behind"""
    def __init__(self, x, y, facing_right):
        self.x = x
        self.y = y
        self.facing_right = facing_right
        self.life = 180  # Frames until fade out

    def update(self):
        self.life -= 1

    def draw(self, surface, camera_x, camera_y):
        if self.life <= 0:
            return
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        if 0 < screen_x < SCREEN_WIDTH and 0 < screen_y < SCREEN_HEIGHT:
            alpha = min(255, self.life * 2)
            color = (100, 180, 100)
            size = 6
            # Two little ovals for footprint
            offset = 4 if self.facing_right else -4
            pygame.draw.ellipse(surface, color, (int(screen_x - 3 + offset), int(screen_y - 4), 6, 8))
            pygame.draw.ellipse(surface, color, (int(screen_x - 3 - offset), int(screen_y - 2), 6, 8))

class Character:
    """The cute character that walks around"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.facing_right = True
        self.walking = False
        self.walk_time = 0
        self.size = 40
        # Colors for a cute bunny character
        self.body_color = (255, 240, 245)  # Light pink/white
        self.ear_color = (255, 200, 210)
        self.cheek_color = (255, 180, 190)

    def update(self, dx, dy):
        self.walking = (dx != 0 or dy != 0)

        if self.walking:
            self.walk_time += 1
            # Update facing direction
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False

        # Move character
        self.x += dx * self.speed
        self.y += dy * self.speed

    def draw(self, surface, screen_x, screen_y):
        # Bounce when walking
        bounce = 0
        if self.walking:
            bounce = abs(math.sin(self.walk_time * 0.3)) * 5

        draw_y = screen_y - bounce

        # Shadow
        shadow_stretch = 1 + bounce * 0.02
        pygame.draw.ellipse(surface, (100, 160, 100),
                          (int(screen_x - 25 * shadow_stretch), int(screen_y + 30),
                           int(50 * shadow_stretch), 15))

        # Body
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x - 25), int(draw_y - 10), 50, 45))

        # Head
        pygame.draw.circle(surface, self.body_color, (int(screen_x), int(draw_y - 30)), 30)

        # Ears
        ear_offset = 15 if self.facing_right else -15
        # Left ear
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x - 20), int(draw_y - 75), 16, 40))
        pygame.draw.ellipse(surface, self.ear_color,
                          (int(screen_x - 17), int(draw_y - 70), 10, 30))
        # Right ear
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x + 4), int(draw_y - 75), 16, 40))
        pygame.draw.ellipse(surface, self.ear_color,
                          (int(screen_x + 7), int(draw_y - 70), 10, 30))

        # Face
        eye_x_offset = 10 if self.facing_right else -10

        # Eyes (cute and big)
        pygame.draw.circle(surface, (0, 0, 0), (int(screen_x - 10 + eye_x_offset//2), int(draw_y - 35)), 8)
        pygame.draw.circle(surface, (0, 0, 0), (int(screen_x + 10 + eye_x_offset//2), int(draw_y - 35)), 8)
        # Eye shine
        pygame.draw.circle(surface, WHITE, (int(screen_x - 12 + eye_x_offset//2), int(draw_y - 37)), 3)
        pygame.draw.circle(surface, WHITE, (int(screen_x + 8 + eye_x_offset//2), int(draw_y - 37)), 3)

        # Cheeks
        pygame.draw.circle(surface, self.cheek_color, (int(screen_x - 22), int(draw_y - 25)), 8)
        pygame.draw.circle(surface, self.cheek_color, (int(screen_x + 22), int(draw_y - 25)), 8)

        # Nose
        pygame.draw.circle(surface, (255, 150, 160), (int(screen_x + eye_x_offset//2), int(draw_y - 25)), 5)

        # Mouth (little smile)
        pygame.draw.arc(surface, (200, 100, 120),
                       (int(screen_x - 8 + eye_x_offset//2), int(draw_y - 22), 16, 10),
                       3.14, 2 * 3.14, 2)

        # Little tail
        tail_x = screen_x - 20 if self.facing_right else screen_x + 20
        pygame.draw.circle(surface, self.body_color, (int(tail_x), int(draw_y + 15)), 12)

        # Feet (bouncy when walking)
        foot_offset = math.sin(self.walk_time * 0.3) * 5 if self.walking else 0
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x - 22), int(screen_y + 25 + foot_offset), 18, 12))
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x + 4), int(screen_y + 25 - foot_offset), 18, 12))

def main():
    clock = pygame.time.Clock()

    # World size (bigger than screen for exploration)
    WORLD_WIDTH = SCREEN_WIDTH * 3
    WORLD_HEIGHT = SCREEN_HEIGHT * 2

    # Create character in center of world
    character = Character(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)

    # Create world objects
    flowers = [Flower(random.randint(0, WORLD_WIDTH),
                     random.randint(SCREEN_HEIGHT // 2, WORLD_HEIGHT))
               for _ in range(150)]

    butterflies = [Butterfly(random.randint(0, WORLD_WIDTH),
                            random.randint(0, WORLD_HEIGHT // 2))
                   for _ in range(20)]

    clouds = [Cloud(random.randint(-200, SCREEN_WIDTH + 200),
                   random.randint(50, 200))
              for _ in range(8)]

    footprints = []
    footprint_timer = 0

    # Controller setup
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Controller connected: {joystick.get_name()}")

    deadzone = 0.2

    # Font
    try:
        small_font = pygame.font.SysFont('Arial', 24)
    except:
        small_font = pygame.font.Font(None, 24)

    pygame.mouse.set_visible(False)
    running = True

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Get input
        dx, dy = 0, 0

        # Keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        # Controller input
        if joystick:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)

            if abs(axis_x) > deadzone:
                dx += axis_x
            if abs(axis_y) > deadzone:
                dy += axis_y

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length

        # Update character
        character.update(dx, dy)

        # Keep character in world bounds
        character.x = max(50, min(WORLD_WIDTH - 50, character.x))
        character.y = max(SCREEN_HEIGHT // 2, min(WORLD_HEIGHT - 50, character.y))

        # Create footprints while walking
        if character.walking:
            footprint_timer += 1
            if footprint_timer >= 15:
                footprints.append(Footprint(character.x, character.y + 35, character.facing_right))
                footprint_timer = 0

        # Camera follows character
        camera_x = character.x - SCREEN_WIDTH // 2
        camera_y = character.y - SCREEN_HEIGHT // 2
        camera_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, camera_x))
        camera_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, camera_y))

        # Update world objects
        for flower in flowers:
            flower.update()
        for butterfly in butterflies:
            butterfly.update()
            # Keep butterflies in world
            butterfly.x = max(0, min(WORLD_WIDTH, butterfly.x))
            butterfly.y = max(50, min(WORLD_HEIGHT // 2, butterfly.y))
        for cloud in clouds:
            cloud.update()
        for footprint in footprints[:]:
            footprint.update()
            if footprint.life <= 0:
                footprints.remove(footprint)

        # Draw
        # Sky gradient
        for y in range(SCREEN_HEIGHT // 2):
            ratio = y / (SCREEN_HEIGHT // 2)
            color = (
                int(100 + 35 * ratio),
                int(180 + 26 * ratio),
                int(255 - 20 * ratio)
            )
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

        # Grass
        pygame.draw.rect(screen, GRASS_GREEN, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

        # Sun
        sun_x = SCREEN_WIDTH - 150
        sun_y = 100
        pygame.draw.circle(screen, SUN_YELLOW, (sun_x, sun_y), 60)
        # Sun rays
        for i in range(12):
            angle = i * math.pi / 6 + pygame.time.get_ticks() * 0.001
            ray_x = sun_x + math.cos(angle) * 80
            ray_y = sun_y + math.sin(angle) * 80
            pygame.draw.line(screen, SUN_YELLOW, (sun_x, sun_y), (int(ray_x), int(ray_y)), 4)

        # Clouds
        for cloud in clouds:
            cloud.draw(screen, camera_x, camera_y)

        # Footprints
        for footprint in footprints:
            footprint.draw(screen, camera_x, camera_y)

        # Flowers
        for flower in flowers:
            flower.draw(screen, camera_x, camera_y)

        # Character
        screen_x = character.x - camera_x
        screen_y = character.y - camera_y
        character.draw(screen, screen_x, screen_y)

        # Butterflies (in front of character)
        for butterfly in butterflies:
            butterfly.draw(screen, camera_x, camera_y)

        # Exit hint
        hint_text = small_font.render("Press ESC to exit | Arrow Keys or Left Stick to move", True, (80, 80, 80))
        screen.blit(hint_text, (SCREEN_WIDTH - 420, SCREEN_HEIGHT - 30))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
