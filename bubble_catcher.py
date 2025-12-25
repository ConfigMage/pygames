"""
Bubble Catcher Game
A bunny catches falling bubbles in a basket! Different colors = different points.
Designed for 5-6 year olds with gentle difficulty progression.
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
pygame.display.set_caption("Bubble Catcher!")

# Colors
SKY_BLUE = (135, 206, 250)
GRASS_GREEN = (124, 205, 124)
WHITE = (255, 255, 255)

BUBBLE_COLORS = [
    ((255, 107, 107), 1),    # Red - 1 point
    ((255, 180, 100), 2),    # Orange - 2 points
    ((255, 234, 167), 3),    # Yellow - 3 points
    ((162, 155, 254), 4),    # Purple - 4 points
    ((255, 105, 180), 5),    # Pink - 5 points (rare)
]

class Particle:
    """Sparkle effect when catching bubbles"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2
        self.life = 25
        self.size = random.randint(3, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1
        self.size = max(1, self.size - 0.2)

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class Bubble:
    """A falling bubble to catch"""
    def __init__(self, speed_multiplier=1.0):
        self.radius = random.randint(25, 45)
        self.x = random.randint(self.radius + 50, SCREEN_WIDTH - self.radius - 50)
        self.y = -self.radius
        color_data = random.choices(BUBBLE_COLORS, weights=[40, 30, 15, 10, 5])[0]
        self.color = color_data[0]
        self.points = color_data[1]
        self.speed = random.uniform(2, 4) * speed_multiplier
        self.wobble_offset = random.uniform(0, 2 * math.pi)
        self.wobble_speed = random.uniform(0.03, 0.06)
        self.time = 0
        self.highlight_color = tuple(min(255, c + 60) for c in self.color)

    def update(self):
        self.y += self.speed
        self.time += 1
        self.x += math.sin(self.time * self.wobble_speed + self.wobble_offset) * 1.5

    def draw(self, surface):
        # Main bubble
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Highlight
        highlight_x = int(self.x - self.radius * 0.3)
        highlight_y = int(self.y - self.radius * 0.3)
        pygame.draw.circle(surface, self.highlight_color, (highlight_x, highlight_y), int(self.radius * 0.3))
        # Small shine
        pygame.draw.circle(surface, WHITE, (int(self.x - self.radius * 0.15), int(self.y - self.radius * 0.5)), int(self.radius * 0.12))
        # Point indicator
        if self.points > 1:
            font = pygame.font.Font(None, int(self.radius * 0.8))
            text = font.render(str(self.points), True, WHITE)
            text_rect = text.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(text, text_rect)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + self.radius

class Cloud:
    """Background clouds"""
    def __init__(self):
        self.x = random.randint(-100, SCREEN_WIDTH + 100)
        self.y = random.randint(30, 180)
        self.speed = random.uniform(0.2, 0.5)
        self.size = random.uniform(0.6, 1.2)

    def update(self):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 150:
            self.x = -150
            self.y = random.randint(30, 180)

    def draw(self, surface):
        size = int(35 * self.size)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), size)
        pygame.draw.circle(surface, WHITE, (int(self.x - size * 0.6), int(self.y + 8)), int(size * 0.7))
        pygame.draw.circle(surface, WHITE, (int(self.x + size * 0.6), int(self.y + 5)), int(size * 0.75))

class Bunny:
    """The player's bunny with basket"""
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 120
        self.speed = 8
        self.basket_width = 120
        self.basket_height = 60
        self.moving = False
        self.move_time = 0
        self.facing_right = True
        # Colors
        self.body_color = (255, 240, 245)
        self.ear_color = (255, 200, 210)
        self.cheek_color = (255, 180, 190)
        self.basket_color = (139, 90, 43)
        self.basket_light = (185, 130, 80)

    def update(self, dx):
        self.moving = dx != 0
        if self.moving:
            self.move_time += 1
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False

        self.x += dx * self.speed
        self.x = max(self.basket_width // 2 + 20, min(SCREEN_WIDTH - self.basket_width // 2 - 20, self.x))

    def draw(self, surface):
        bounce = abs(math.sin(self.move_time * 0.2)) * 4 if self.moving else 0
        draw_y = self.y - bounce

        # Shadow
        pygame.draw.ellipse(surface, (100, 170, 100),
                          (int(self.x - 40), int(self.y + 45), 80, 20))

        # Basket (behind bunny)
        basket_x = self.x - self.basket_width // 2
        basket_y = draw_y + 20
        # Basket body
        pygame.draw.ellipse(surface, self.basket_color,
                          (int(basket_x), int(basket_y), self.basket_width, self.basket_height))
        # Basket rim
        pygame.draw.ellipse(surface, self.basket_light,
                          (int(basket_x), int(basket_y - 5), self.basket_width, 20))
        # Basket weave pattern
        for i in range(5):
            line_x = basket_x + 15 + i * 22
            pygame.draw.line(surface, self.basket_light,
                           (int(line_x), int(basket_y + 10)),
                           (int(line_x), int(basket_y + self.basket_height - 15)), 2)

        # Bunny body
        pygame.draw.ellipse(surface, self.body_color,
                          (int(self.x - 25), int(draw_y - 15), 50, 45))

        # Bunny head
        pygame.draw.circle(surface, self.body_color, (int(self.x), int(draw_y - 35)), 28)

        # Ears
        ear_lean = 3 if self.facing_right else -3
        pygame.draw.ellipse(surface, self.body_color,
                          (int(self.x - 18 + ear_lean), int(draw_y - 80), 14, 38))
        pygame.draw.ellipse(surface, self.ear_color,
                          (int(self.x - 15 + ear_lean), int(draw_y - 75), 8, 28))
        pygame.draw.ellipse(surface, self.body_color,
                          (int(self.x + 4 + ear_lean), int(draw_y - 80), 14, 38))
        pygame.draw.ellipse(surface, self.ear_color,
                          (int(self.x + 7 + ear_lean), int(draw_y - 75), 8, 28))

        # Face
        eye_offset = 3 if self.facing_right else -3
        # Eyes
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x - 10 + eye_offset), int(draw_y - 40)), 6)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x + 10 + eye_offset), int(draw_y - 40)), 6)
        pygame.draw.circle(surface, WHITE, (int(self.x - 12 + eye_offset), int(draw_y - 42)), 2)
        pygame.draw.circle(surface, WHITE, (int(self.x + 8 + eye_offset), int(draw_y - 42)), 2)
        # Cheeks
        pygame.draw.circle(surface, self.cheek_color, (int(self.x - 20), int(draw_y - 30)), 6)
        pygame.draw.circle(surface, self.cheek_color, (int(self.x + 20), int(draw_y - 30)), 6)
        # Nose
        pygame.draw.circle(surface, (255, 150, 160), (int(self.x + eye_offset), int(draw_y - 30)), 4)
        # Smile
        pygame.draw.arc(surface, (200, 100, 120),
                       (int(self.x - 8 + eye_offset), int(draw_y - 28), 16, 10), 3.14, 2 * 3.14, 2)

        # Arms holding basket
        pygame.draw.ellipse(surface, self.body_color,
                          (int(self.x - 45), int(draw_y + 5), 25, 15))
        pygame.draw.ellipse(surface, self.body_color,
                          (int(self.x + 20), int(draw_y + 5), 25, 15))

    def get_basket_rect(self):
        """Get the catching area"""
        return pygame.Rect(
            self.x - self.basket_width // 2,
            self.y + 10,
            self.basket_width,
            self.basket_height // 2
        )

def create_catch_sound():
    """Create a pleasant catch sound"""
    try:
        sample_rate = 22050
        duration = 0.15
        samples = int(sample_rate * duration)
        import array
        buf = array.array('h')
        for i in range(samples):
            t = i / sample_rate
            freq = 600 + t * 800
            amplitude = int(32767 * (1 - t / duration) * 0.25)
            value = int(amplitude * math.sin(2 * math.pi * freq * t))
            buf.append(value)
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(0.3)
        return sound
    except:
        return None

def create_miss_sound():
    """Create a soft 'aww' sound for missed bubbles"""
    try:
        sample_rate = 22050
        duration = 0.2
        samples = int(sample_rate * duration)
        import array
        buf = array.array('h')
        for i in range(samples):
            t = i / sample_rate
            freq = 300 - t * 150
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

    bunny = Bunny()
    bubbles = []
    particles = []
    clouds = [Cloud() for _ in range(6)]

    score = 0
    missed = 0
    max_misses = 10  # Forgiving for young kids
    spawn_timer = 0
    spawn_rate = 90  # Frames between spawns
    speed_multiplier = 1.0

    catch_sound = create_catch_sound()
    miss_sound = create_miss_sound()

    # Controller setup
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Controller connected: {joystick.get_name()}")

    deadzone = 0.2

    # Fonts
    try:
        font = pygame.font.SysFont('Arial Rounded MT Bold', 64)
        small_font = pygame.font.SysFont('Arial', 28)
    except:
        font = pygame.font.Font(None, 64)
        small_font = pygame.font.Font(None, 28)

    pygame.mouse.set_visible(False)
    running = True
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and game_over:
                    # Restart
                    score = 0
                    missed = 0
                    bubbles = []
                    particles = []
                    speed_multiplier = 1.0
                    spawn_rate = 90
                    game_over = False

        if not game_over:
            # Get input
            dx = 0

            # Keyboard
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += 1

            # Controller
            if joystick:
                axis_x = joystick.get_axis(0)
                if abs(axis_x) > deadzone:
                    dx += axis_x * 1.5  # Smoother controller movement

                # D-pad support
                try:
                    hat = joystick.get_hat(0)
                    dx += hat[0]
                except:
                    pass

            # Clamp dx
            dx = max(-1.5, min(1.5, dx))

            # Update bunny
            bunny.update(dx)

            # Spawn bubbles
            spawn_timer += 1
            if spawn_timer >= spawn_rate:
                bubbles.append(Bubble(speed_multiplier))
                spawn_timer = 0

            # Update bubbles
            basket_rect = bunny.get_basket_rect()
            for bubble in bubbles[:]:
                bubble.update()

                # Check if caught
                bubble_rect = pygame.Rect(
                    bubble.x - bubble.radius,
                    bubble.y - bubble.radius,
                    bubble.radius * 2,
                    bubble.radius * 2
                )

                if basket_rect.colliderect(bubble_rect) and bubble.y > bunny.y:
                    bubbles.remove(bubble)
                    score += bubble.points

                    # Particles
                    for _ in range(12):
                        particles.append(Particle(bubble.x, bubble.y, bubble.color))

                    if catch_sound:
                        catch_sound.play()

                    # Increase difficulty gradually
                    if score % 15 == 0:
                        speed_multiplier = min(2.0, speed_multiplier + 0.1)
                        spawn_rate = max(40, spawn_rate - 5)

                elif bubble.is_off_screen():
                    bubbles.remove(bubble)
                    missed += 1
                    if miss_sound:
                        miss_sound.play()

                    if missed >= max_misses:
                        game_over = True

            # Update particles
            for particle in particles[:]:
                particle.update()
                if particle.life <= 0:
                    particles.remove(particle)

            # Update clouds
            for cloud in clouds:
                cloud.update()

        # Draw
        # Sky gradient
        for y in range(int(SCREEN_HEIGHT * 0.7)):
            ratio = y / (SCREEN_HEIGHT * 0.7)
            color = (
                int(135 + 50 * ratio),
                int(200 + 30 * ratio),
                int(250 - 20 * ratio)
            )
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

        # Ground
        ground_y = int(SCREEN_HEIGHT * 0.7)
        pygame.draw.rect(screen, GRASS_GREEN, (0, ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y))

        # Grass tufts
        for i in range(0, SCREEN_WIDTH, 30):
            height = random.randint(10, 20)
            pygame.draw.polygon(screen, (100, 180, 100), [
                (i, ground_y),
                (i + 10, ground_y - height),
                (i + 20, ground_y)
            ])

        # Clouds
        for cloud in clouds:
            cloud.draw(screen)

        # Bubbles
        for bubble in bubbles:
            bubble.draw(screen)

        # Bunny
        bunny.draw(screen)

        # Particles
        for particle in particles:
            particle.draw(screen)

        # UI
        score_text = font.render(f"Score: {score}", True, (50, 50, 100))
        screen.blit(score_text, (20, 20))

        # Missed counter (hearts remaining)
        hearts_left = max_misses - missed
        heart_text = small_font.render("Lives: " + "❤️ " * hearts_left, True, (200, 50, 50))
        screen.blit(heart_text, (20, 90))

        # Hint
        hint_text = small_font.render("ESC to exit | Arrow Keys or Left Stick to move", True, (80, 80, 80))
        screen.blit(hint_text, (SCREEN_WIDTH - 420, SCREEN_HEIGHT - 35))

        # Game over screen
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))

            game_over_font = pygame.font.Font(None, 100)
            go_text = game_over_font.render("Great Job!", True, WHITE)
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            screen.blit(go_text, go_rect)

            final_score = font.render(f"You caught {score} points!", True, (255, 255, 150))
            fs_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            screen.blit(final_score, fs_rect)

            restart_text = small_font.render("Press SPACE to play again!", True, WHITE)
            rs_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
            screen.blit(restart_text, rs_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
