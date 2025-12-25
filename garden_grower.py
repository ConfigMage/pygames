"""
Garden Grower Game
Walk around your garden, plant seeds, water them, and watch flowers bloom!
Butterflies visit your beautiful flowers. Designed for 5-6 year olds.
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
pygame.display.set_caption("Garden Grower!")

# Colors
SKY_BLUE = (180, 220, 255)
GRASS_GREEN = (140, 200, 100)
DIRT_BROWN = (139, 90, 60)
WHITE = (255, 255, 255)
SUN_YELLOW = (255, 230, 100)

FLOWER_COLORS = [
    (255, 107, 107),   # Red
    (255, 159, 243),   # Pink
    (255, 200, 100),   # Orange
    (200, 162, 255),   # Purple
    (255, 255, 150),   # Yellow
    (150, 200, 255),   # Light Blue
]

class Particle:
    """Sparkle particles for planting/watering"""
    def __init__(self, x, y, color, going_up=True):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 4)
        self.vx = math.cos(angle) * speed
        self.vy = -abs(math.sin(angle) * speed) if going_up else math.sin(angle) * speed
        self.life = 30
        self.size = random.randint(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1

    def draw(self, surface, camera_x, camera_y):
        if self.life > 0:
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            if 0 < screen_x < SCREEN_WIDTH and 0 < screen_y < SCREEN_HEIGHT:
                pygame.draw.circle(surface, self.color, (int(screen_x), int(screen_y)), int(self.size * (self.life / 30)))

class PlantSpot:
    """A spot where you can plant"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = "empty"  # empty, seed, growing, flower
        self.color = random.choice(FLOWER_COLORS)
        self.growth_timer = 0
        self.growth_stage = 0
        self.sway_offset = random.uniform(0, 2 * math.pi)
        self.petals = random.randint(5, 8)
        self.size = random.randint(15, 25)

    def plant_seed(self):
        if self.state == "empty":
            self.state = "seed"
            self.growth_timer = 0
            return True
        return False

    def water(self):
        if self.state == "seed":
            self.state = "growing"
            self.growth_timer = 0
            self.growth_stage = 0
            return True
        return False

    def update(self):
        if self.state == "growing":
            self.growth_timer += 1
            if self.growth_timer > 30:
                self.growth_stage += 1
                self.growth_timer = 0
                if self.growth_stage >= 4:
                    self.state = "flower"

    def draw(self, surface, camera_x, camera_y, time):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        if -50 < screen_x < SCREEN_WIDTH + 50 and -50 < screen_y < SCREEN_HEIGHT + 50:
            # Dirt mound (always visible)
            pygame.draw.ellipse(surface, DIRT_BROWN,
                              (int(screen_x - 20), int(screen_y - 5), 40, 15))
            pygame.draw.ellipse(surface, (160, 110, 80),
                              (int(screen_x - 18), int(screen_y - 8), 36, 10))

            if self.state == "empty":
                # Show a little hole indicator
                pygame.draw.ellipse(surface, (100, 60, 40),
                                  (int(screen_x - 8), int(screen_y - 5), 16, 8))

            elif self.state == "seed":
                # Show seed
                pygame.draw.ellipse(surface, (80, 50, 30),
                                  (int(screen_x - 5), int(screen_y - 8), 10, 8))
                # Water droplet indicator
                pygame.draw.polygon(surface, (100, 180, 255), [
                    (int(screen_x + 15), int(screen_y - 25)),
                    (int(screen_x + 10), int(screen_y - 15)),
                    (int(screen_x + 20), int(screen_y - 15)),
                ])

            elif self.state == "growing":
                # Growing plant
                stem_height = 10 + self.growth_stage * 15
                pygame.draw.line(surface, (80, 160, 80),
                               (int(screen_x), int(screen_y - 5)),
                               (int(screen_x), int(screen_y - stem_height)), 3)
                # Small leaves
                if self.growth_stage >= 2:
                    pygame.draw.ellipse(surface, (100, 180, 100),
                                      (int(screen_x - 12), int(screen_y - stem_height + 10), 12, 8))
                    pygame.draw.ellipse(surface, (100, 180, 100),
                                      (int(screen_x), int(screen_y - stem_height + 15), 12, 8))
                # Bud
                if self.growth_stage >= 3:
                    pygame.draw.circle(surface, self.color,
                                     (int(screen_x), int(screen_y - stem_height)), 8)

            elif self.state == "flower":
                # Full flower with sway
                sway = math.sin(time * 0.02 + self.sway_offset) * 3

                # Stem
                pygame.draw.line(surface, (80, 160, 80),
                               (int(screen_x), int(screen_y - 5)),
                               (int(screen_x + sway), int(screen_y - 60)), 4)

                # Leaves
                pygame.draw.ellipse(surface, (100, 180, 100),
                                  (int(screen_x - 15 + sway * 0.3), int(screen_y - 35), 15, 10))
                pygame.draw.ellipse(surface, (100, 180, 100),
                                  (int(screen_x + sway * 0.3), int(screen_y - 45), 15, 10))

                # Flower petals
                flower_x = screen_x + sway
                flower_y = screen_y - 60
                for i in range(self.petals):
                    angle = (2 * math.pi * i / self.petals) + time * 0.005
                    petal_x = flower_x + math.cos(angle) * self.size
                    petal_y = flower_y + math.sin(angle) * self.size
                    pygame.draw.circle(surface, self.color,
                                     (int(petal_x), int(petal_y)), self.size // 2)

                # Center
                pygame.draw.circle(surface, SUN_YELLOW,
                                 (int(flower_x), int(flower_y)), self.size // 3)

    def is_near(self, x, y, radius=40):
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2) < radius

class Butterfly:
    """Butterflies attracted to flowers"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice([(255, 150, 200), (200, 150, 255), (255, 200, 100), (150, 200, 255)])
        self.time = random.uniform(0, 2 * math.pi)
        self.wing_speed = random.uniform(0.2, 0.35)
        self.target_x = x
        self.target_y = y
        self.speed = 2

    def set_target(self, x, y):
        self.target_x = x
        self.target_y = y + random.randint(-30, -10)  # Hover above target

    def update(self):
        self.time += 1

        # Move toward target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 5:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        # Flutter
        self.y += math.sin(self.time * 0.1) * 0.5

    def draw(self, surface, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        if -30 < screen_x < SCREEN_WIDTH + 30 and -30 < screen_y < SCREEN_HEIGHT + 30:
            wing_flap = abs(math.sin(self.time * self.wing_speed))
            wing_size = int(10 * wing_flap) + 5

            # Wings
            pygame.draw.ellipse(surface, self.color,
                              (int(screen_x - wing_size - 2), int(screen_y - 5), wing_size, 10))
            pygame.draw.ellipse(surface, self.color,
                              (int(screen_x + 2), int(screen_y - 5), wing_size, 10))
            # Body
            pygame.draw.ellipse(surface, (50, 50, 50),
                              (int(screen_x - 2), int(screen_y - 6), 4, 12))

class Cloud:
    """Background clouds"""
    def __init__(self):
        self.x = random.randint(-100, SCREEN_WIDTH + 100)
        self.y = random.randint(30, 150)
        self.speed = random.uniform(0.1, 0.3)
        self.size = random.uniform(0.7, 1.3)

    def update(self):
        self.x += self.speed

    def draw(self, surface, camera_x):
        screen_x = self.x - camera_x * 0.2  # Parallax
        if screen_x > SCREEN_WIDTH + 100:
            self.x -= SCREEN_WIDTH + 200

        size = int(40 * self.size)
        pygame.draw.circle(surface, WHITE, (int(screen_x), int(self.y)), size)
        pygame.draw.circle(surface, WHITE, (int(screen_x - size * 0.6), int(self.y + 8)), int(size * 0.7))
        pygame.draw.circle(surface, WHITE, (int(screen_x + size * 0.6), int(self.y + 5)), int(size * 0.75))

class Character:
    """Gardener bunny"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.facing_right = True
        self.walking = False
        self.walk_time = 0
        self.body_color = (255, 240, 245)
        self.ear_color = (255, 200, 210)
        self.cheek_color = (255, 180, 190)
        # Tool states
        self.has_seeds = True
        self.has_water = True

    def update(self, dx, dy):
        self.walking = (dx != 0 or dy != 0)
        if self.walking:
            self.walk_time += 1
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False

        self.x += dx * self.speed
        self.y += dy * self.speed

    def draw(self, surface, screen_x, screen_y):
        bounce = abs(math.sin(self.walk_time * 0.3)) * 5 if self.walking else 0
        draw_y = screen_y - bounce

        # Shadow
        pygame.draw.ellipse(surface, (100, 160, 80),
                          (int(screen_x - 25), int(screen_y + 30), 50, 15))

        # Body
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x - 25), int(draw_y - 10), 50, 45))

        # Head
        pygame.draw.circle(surface, self.body_color, (int(screen_x), int(draw_y - 30)), 28)

        # Ears
        ear_offset = 3 if self.facing_right else -3
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x - 18 + ear_offset), int(draw_y - 75), 14, 38))
        pygame.draw.ellipse(surface, self.ear_color,
                          (int(screen_x - 15 + ear_offset), int(draw_y - 70), 8, 28))
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x + 4 + ear_offset), int(draw_y - 75), 14, 38))
        pygame.draw.ellipse(surface, self.ear_color,
                          (int(screen_x + 7 + ear_offset), int(draw_y - 70), 8, 28))

        # Face
        eye_x = 3 if self.facing_right else -3
        # Eyes
        pygame.draw.circle(surface, (0, 0, 0), (int(screen_x - 10 + eye_x), int(draw_y - 35)), 6)
        pygame.draw.circle(surface, (0, 0, 0), (int(screen_x + 10 + eye_x), int(draw_y - 35)), 6)
        pygame.draw.circle(surface, WHITE, (int(screen_x - 12 + eye_x), int(draw_y - 37)), 2)
        pygame.draw.circle(surface, WHITE, (int(screen_x + 8 + eye_x), int(draw_y - 37)), 2)
        # Cheeks
        pygame.draw.circle(surface, self.cheek_color, (int(screen_x - 20), int(draw_y - 25)), 6)
        pygame.draw.circle(surface, self.cheek_color, (int(screen_x + 20), int(draw_y - 25)), 6)
        # Nose
        pygame.draw.circle(surface, (255, 150, 160), (int(screen_x + eye_x), int(draw_y - 25)), 4)
        # Smile
        pygame.draw.arc(surface, (200, 100, 120),
                       (int(screen_x - 8 + eye_x), int(draw_y - 22), 16, 10), 3.14, 2 * 3.14, 2)

        # Little gardening apron
        pygame.draw.ellipse(surface, (150, 200, 255),
                          (int(screen_x - 20), int(draw_y + 5), 40, 25))

        # Feet
        foot_offset = math.sin(self.walk_time * 0.3) * 5 if self.walking else 0
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x - 20), int(screen_y + 25 + foot_offset), 16, 10))
        pygame.draw.ellipse(surface, self.body_color,
                          (int(screen_x + 4), int(screen_y + 25 - foot_offset), 16, 10))

def create_plant_sound():
    try:
        sample_rate = 22050
        duration = 0.1
        samples = int(sample_rate * duration)
        import array
        buf = array.array('h')
        for i in range(samples):
            t = i / sample_rate
            freq = 400 + t * 600
            amplitude = int(32767 * (1 - t / duration) * 0.2)
            value = int(amplitude * math.sin(2 * math.pi * freq * t))
            buf.append(value)
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(0.25)
        return sound
    except:
        return None

def create_water_sound():
    try:
        sample_rate = 22050
        duration = 0.2
        samples = int(sample_rate * duration)
        import array
        buf = array.array('h')
        for i in range(samples):
            t = i / sample_rate
            freq = 200 + random.randint(-50, 50)
            amplitude = int(32767 * (1 - t / duration) * 0.15)
            value = int(amplitude * math.sin(2 * math.pi * freq * t))
            buf.append(value)
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(0.2)
        return sound
    except:
        return None

def main():
    clock = pygame.time.Clock()

    # World size
    WORLD_WIDTH = SCREEN_WIDTH * 2
    WORLD_HEIGHT = int(SCREEN_HEIGHT * 1.5)
    GROUND_Y = SCREEN_HEIGHT // 2

    # Create character
    character = Character(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)

    # Create planting spots in a grid pattern
    plant_spots = []
    spot_spacing = 120
    for row in range(6):
        for col in range(12):
            x = 150 + col * spot_spacing + random.randint(-20, 20)
            y = GROUND_Y + 100 + row * 100 + random.randint(-15, 15)
            plant_spots.append(PlantSpot(x, y))

    butterflies = []
    particles = []
    clouds = [Cloud() for _ in range(8)]
    time_counter = 0

    # Sounds
    plant_sound = create_plant_sound()
    water_sound = create_water_sound()

    # Controller
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Controller connected: {joystick.get_name()}")

    deadzone = 0.2

    # Fonts
    try:
        font = pygame.font.SysFont('Arial Rounded MT Bold', 48)
        small_font = pygame.font.SysFont('Arial', 24)
    except:
        font = pygame.font.Font(None, 48)
        small_font = pygame.font.Font(None, 24)

    pygame.mouse.set_visible(False)
    running = True
    a_button_pressed = False
    b_button_pressed = False

    # Stats
    flowers_grown = 0

    while running:
        time_counter += 1

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE or event.key == pygame.K_z:
                    # Plant seed
                    for spot in plant_spots:
                        if spot.is_near(character.x, character.y):
                            if spot.plant_seed():
                                for _ in range(8):
                                    particles.append(Particle(spot.x, spot.y - 10, DIRT_BROWN, False))
                                if plant_sound:
                                    plant_sound.play()
                                break
                elif event.key == pygame.K_x or event.key == pygame.K_RETURN:
                    # Water plant
                    for spot in plant_spots:
                        if spot.is_near(character.x, character.y):
                            if spot.water():
                                for _ in range(10):
                                    particles.append(Particle(spot.x, spot.y - 20, (100, 180, 255), True))
                                if water_sound:
                                    water_sound.play()
                                break

        # Movement input
        dx, dy = 0, 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        # Controller
        if joystick:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)

            if abs(axis_x) > deadzone:
                dx += axis_x
            if abs(axis_y) > deadzone:
                dy += axis_y

            # A button = plant
            a_now = joystick.get_button(0)
            if a_now and not a_button_pressed:
                for spot in plant_spots:
                    if spot.is_near(character.x, character.y):
                        if spot.plant_seed():
                            for _ in range(8):
                                particles.append(Particle(spot.x, spot.y - 10, DIRT_BROWN, False))
                            if plant_sound:
                                plant_sound.play()
                            break
            a_button_pressed = a_now

            # B/X button = water
            b_now = joystick.get_button(1) or joystick.get_button(2)
            if b_now and not b_button_pressed:
                for spot in plant_spots:
                    if spot.is_near(character.x, character.y):
                        if spot.water():
                            for _ in range(10):
                                particles.append(Particle(spot.x, spot.y - 20, (100, 180, 255), True))
                            if water_sound:
                                water_sound.play()
                            break
            b_button_pressed = b_now

        # Normalize diagonal
        if dx != 0 and dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length

        character.update(dx, dy)

        # Keep in bounds
        character.x = max(50, min(WORLD_WIDTH - 50, character.x))
        character.y = max(GROUND_Y + 50, min(WORLD_HEIGHT - 50, character.y))

        # Update plant spots
        old_flowers = flowers_grown
        flowers_grown = 0
        for spot in plant_spots:
            spot.update()
            if spot.state == "flower":
                flowers_grown += 1

        # Spawn butterfly when new flower blooms
        if flowers_grown > old_flowers:
            new_butterfly = Butterfly(
                random.randint(0, WORLD_WIDTH),
                random.randint(GROUND_Y - 100, GROUND_Y)
            )
            butterflies.append(new_butterfly)

        # Update butterflies - they go to flowers
        flower_spots = [s for s in plant_spots if s.state == "flower"]
        for butterfly in butterflies:
            # Occasionally pick a new target
            if random.random() < 0.01 and flower_spots:
                target = random.choice(flower_spots)
                butterfly.set_target(target.x, target.y - 50)
            butterfly.update()

        # Update particles
        for particle in particles[:]:
            particle.update()
            if particle.life <= 0:
                particles.remove(particle)

        # Update clouds
        for cloud in clouds:
            cloud.update()

        # Camera
        camera_x = character.x - SCREEN_WIDTH // 2
        camera_y = character.y - SCREEN_HEIGHT // 2
        camera_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, camera_x))
        camera_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, camera_y))

        # Draw
        # Sky
        screen.fill(SKY_BLUE)

        # Sun
        sun_x = SCREEN_WIDTH - 100
        sun_y = 80
        pygame.draw.circle(screen, SUN_YELLOW, (sun_x, sun_y), 50)
        for i in range(12):
            angle = i * math.pi / 6 + time_counter * 0.01
            ray_x = sun_x + math.cos(angle) * 70
            ray_y = sun_y + math.sin(angle) * 70
            pygame.draw.line(screen, SUN_YELLOW, (sun_x, sun_y), (int(ray_x), int(ray_y)), 3)

        # Clouds
        for cloud in clouds:
            cloud.draw(screen, camera_x)

        # Ground
        ground_screen_y = GROUND_Y - camera_y
        pygame.draw.rect(screen, GRASS_GREEN,
                        (0, ground_screen_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_screen_y))

        # Fence at top of garden
        fence_y = GROUND_Y + 50 - camera_y
        for x in range(0, SCREEN_WIDTH + 50, 40):
            pygame.draw.rect(screen, (160, 120, 80), (x, int(fence_y), 8, 40))
            pygame.draw.polygon(screen, (160, 120, 80), [
                (x, int(fence_y)),
                (x + 4, int(fence_y - 15)),
                (x + 8, int(fence_y))
            ])
        pygame.draw.rect(screen, (140, 100, 60), (0, int(fence_y + 10), SCREEN_WIDTH, 6))
        pygame.draw.rect(screen, (140, 100, 60), (0, int(fence_y + 30), SCREEN_WIDTH, 6))

        # Plant spots
        for spot in plant_spots:
            spot.draw(screen, camera_x, camera_y, time_counter)

        # Character
        char_screen_x = character.x - camera_x
        char_screen_y = character.y - camera_y
        character.draw(screen, char_screen_x, char_screen_y)

        # Butterflies
        for butterfly in butterflies:
            butterfly.draw(screen, camera_x, camera_y)

        # Particles
        for particle in particles:
            particle.draw(screen, camera_x, camera_y)

        # UI
        flower_text = font.render(f"Flowers: {flowers_grown}", True, (80, 60, 40))
        screen.blit(flower_text, (20, 20))

        # Controls hint
        hint1 = small_font.render("Move: Arrow Keys / Left Stick", True, (80, 80, 80))
        hint2 = small_font.render("Plant: SPACE / A Button | Water: X / B Button", True, (80, 80, 80))
        screen.blit(hint1, (20, SCREEN_HEIGHT - 55))
        screen.blit(hint2, (20, SCREEN_HEIGHT - 30))

        # ESC hint
        esc_hint = small_font.render("ESC to exit", True, (80, 80, 80))
        screen.blit(esc_hint, (SCREEN_WIDTH - 120, 20))

        # Nearby spot indicator
        for spot in plant_spots:
            if spot.is_near(character.x, character.y):
                screen_x = spot.x - camera_x
                screen_y = spot.y - camera_y - 80
                if spot.state == "empty":
                    prompt = small_font.render("Press A/SPACE to plant!", True, (50, 120, 50))
                    screen.blit(prompt, (int(screen_x - 80), int(screen_y)))
                elif spot.state == "seed":
                    prompt = small_font.render("Press B/X to water!", True, (50, 100, 180))
                    screen.blit(prompt, (int(screen_x - 70), int(screen_y)))
                break

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
