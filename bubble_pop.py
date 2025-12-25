"""
Bubble Pop Game for Toddlers
A simple, colorful game where clicking bubbles makes them pop!
Perfect for 3-year-olds learning to use a mouse or Xbox controller.
"""

import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init()
pygame.joystick.init()

# Screen setup - fullscreen for immersive experience
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Bubble Pop! 🫧")

# Colors - bright and cheerful for kids
COLORS = [
    (255, 107, 107),   # Coral Red
    (255, 159, 243),   # Pink
    (162, 155, 254),   # Lavender
    (95, 234, 182),    # Mint Green
    (255, 234, 167),   # Soft Yellow
    (116, 185, 255),   # Sky Blue
    (255, 177, 66),    # Orange
    (99, 230, 226),    # Turquoise
]

BACKGROUND_COLOR = (25, 25, 50)  # Dark blue background

# Game settings
MAX_BUBBLES = 15
BUBBLE_SPAWN_RATE = 60  # frames between spawns
MIN_BUBBLE_SIZE = 40
MAX_BUBBLE_SIZE = 100

class Particle:
    """Small sparkle particles for pop effects"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 30
        self.size = random.randint(4, 10)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # gravity
        self.life -= 1
        self.size = max(1, self.size - 0.3)

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * (self.life / 30))
            color = (*self.color[:3], alpha)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class Bubble:
    """A floating bubble that can be popped"""
    def __init__(self):
        self.radius = random.randint(MIN_BUBBLE_SIZE, MAX_BUBBLE_SIZE)
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = SCREEN_HEIGHT + self.radius
        self.color = random.choice(COLORS)
        self.speed = random.uniform(1, 3)
        self.wobble_offset = random.uniform(0, 2 * math.pi)
        self.wobble_speed = random.uniform(0.02, 0.05)
        self.time = 0
        self.highlight_color = tuple(min(255, c + 60) for c in self.color)

    def update(self):
        self.y -= self.speed
        self.time += 1
        # Gentle side-to-side wobble
        self.x += math.sin(self.time * self.wobble_speed + self.wobble_offset) * 0.5

    def draw(self, surface):
        # Main bubble
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

        # Highlight (makes it look 3D and shiny)
        highlight_x = int(self.x - self.radius * 0.3)
        highlight_y = int(self.y - self.radius * 0.3)
        highlight_radius = int(self.radius * 0.3)
        pygame.draw.circle(surface, self.highlight_color, (highlight_x, highlight_y), highlight_radius)

        # Small extra shine
        small_highlight_x = int(self.x - self.radius * 0.15)
        small_highlight_y = int(self.y - self.radius * 0.5)
        pygame.draw.circle(surface, (255, 255, 255), (small_highlight_x, small_highlight_y), int(self.radius * 0.1))

    def contains_point(self, x, y):
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        return distance <= self.radius

    def is_off_screen(self):
        return self.y < -self.radius

class Star:
    """Background twinkling star"""
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(100, 255)
        self.twinkle_speed = random.uniform(0.02, 0.08)
        self.time = random.uniform(0, 2 * math.pi)

    def update(self):
        self.time += self.twinkle_speed

    def draw(self, surface):
        current_brightness = int(self.brightness * (0.5 + 0.5 * math.sin(self.time)))
        color = (current_brightness, current_brightness, current_brightness)
        pygame.draw.circle(surface, color, (self.x, self.y), self.size)

def create_pop_sound():
    """Create a simple pop sound effect"""
    try:
        # Create a simple pop sound using pygame
        sample_rate = 22050
        duration = 0.1
        samples = int(sample_rate * duration)

        # Generate a quick descending tone
        import array
        buf = array.array('h')
        for i in range(samples):
            t = i / sample_rate
            freq = 800 - (t * 4000)  # Descending frequency
            amplitude = int(32767 * (1 - t / duration) * 0.3)
            value = int(amplitude * math.sin(2 * math.pi * freq * t))
            buf.append(value)

        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(0.3)
        return sound
    except:
        return None

def main():
    clock = pygame.time.Clock()
    bubbles = []
    particles = []
    stars = [Star() for _ in range(50)]
    spawn_timer = 0
    score = 0

    # Create pop sound
    pop_sound = create_pop_sound()

    # Xbox controller setup
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Controller connected: {joystick.get_name()}")

    # Custom cursor position (for controller)
    cursor_x = SCREEN_WIDTH // 2
    cursor_y = SCREEN_HEIGHT // 2
    cursor_speed = 15  # How fast the cursor moves
    deadzone = 0.2  # Ignore small stick movements

    # Font for score (big and friendly)
    try:
        font = pygame.font.SysFont('Arial Rounded MT Bold', 72)
        small_font = pygame.font.SysFont('Arial', 24)
    except:
        font = pygame.font.Font(None, 72)
        small_font = pygame.font.Font(None, 24)

    running = True
    a_button_pressed = False  # Track button state to avoid repeat triggers

    # Hide system cursor - we draw our own
    pygame.mouse.set_visible(False)

    # Spawn some initial bubbles
    for _ in range(5):
        bubble = Bubble()
        bubble.y = random.randint(100, SCREEN_HEIGHT - 100)
        bubbles.append(bubble)

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                # Update cursor position to mouse position
                cursor_x, cursor_y = mouse_x, mouse_y
                # Check bubbles from front to back (last added = on top)
                for bubble in reversed(bubbles):
                    if bubble.contains_point(mouse_x, mouse_y):
                        # Pop the bubble!
                        bubbles.remove(bubble)
                        score += 1

                        # Create particles
                        for _ in range(15):
                            particles.append(Particle(bubble.x, bubble.y, bubble.color))

                        # Play sound
                        if pop_sound:
                            pop_sound.play()

                        break  # Only pop one bubble per click
            elif event.type == pygame.MOUSEMOTION:
                # Keep cursor synced with mouse
                cursor_x, cursor_y = event.pos

        # Xbox controller input
        if joystick:
            # Left analog stick moves cursor
            axis_x = joystick.get_axis(0)  # Left stick horizontal
            axis_y = joystick.get_axis(1)  # Left stick vertical

            # Apply deadzone
            if abs(axis_x) > deadzone:
                cursor_x += axis_x * cursor_speed
            if abs(axis_y) > deadzone:
                cursor_y += axis_y * cursor_speed

            # Keep cursor on screen
            cursor_x = max(0, min(SCREEN_WIDTH, cursor_x))
            cursor_y = max(0, min(SCREEN_HEIGHT, cursor_y))

            # A button (button 0) to pop bubbles
            a_button_now = joystick.get_button(0)
            if a_button_now and not a_button_pressed:
                # Check bubbles at cursor position
                for bubble in reversed(bubbles):
                    if bubble.contains_point(cursor_x, cursor_y):
                        bubbles.remove(bubble)
                        score += 1
                        for _ in range(15):
                            particles.append(Particle(bubble.x, bubble.y, bubble.color))
                        if pop_sound:
                            pop_sound.play()
                        break
            a_button_pressed = a_button_now

        # Spawn new bubbles
        spawn_timer += 1
        if spawn_timer >= BUBBLE_SPAWN_RATE and len(bubbles) < MAX_BUBBLES:
            bubbles.append(Bubble())
            spawn_timer = 0

        # Update
        for star in stars:
            star.update()

        for bubble in bubbles[:]:
            bubble.update()
            if bubble.is_off_screen():
                bubbles.remove(bubble)

        for particle in particles[:]:
            particle.update()
            if particle.life <= 0:
                particles.remove(particle)

        # Draw
        screen.fill(BACKGROUND_COLOR)

        # Draw stars
        for star in stars:
            star.draw(screen)

        # Draw bubbles
        for bubble in bubbles:
            bubble.draw(screen)

        # Draw particles
        for particle in particles:
            particle.draw(screen)

        # Draw score (fun and encouraging)
        score_text = font.render(f"⭐ {score}", True, (255, 255, 255))
        screen.blit(score_text, (20, 20))

        # Draw custom cursor (big and friendly, especially visible with controller)
        cursor_color = (255, 255, 100)  # Bright yellow
        cursor_size = 20
        # Outer ring
        pygame.draw.circle(screen, cursor_color, (int(cursor_x), int(cursor_y)), cursor_size, 4)
        # Inner dot
        pygame.draw.circle(screen, (255, 255, 255), (int(cursor_x), int(cursor_y)), 6)
        # Crosshair lines for visibility
        pygame.draw.line(screen, cursor_color, (int(cursor_x) - cursor_size - 5, int(cursor_y)),
                         (int(cursor_x) - cursor_size + 10, int(cursor_y)), 3)
        pygame.draw.line(screen, cursor_color, (int(cursor_x) + cursor_size - 10, int(cursor_y)),
                         (int(cursor_x) + cursor_size + 5, int(cursor_y)), 3)
        pygame.draw.line(screen, cursor_color, (int(cursor_x), int(cursor_y) - cursor_size - 5),
                         (int(cursor_x), int(cursor_y) - cursor_size + 10), 3)
        pygame.draw.line(screen, cursor_color, (int(cursor_x), int(cursor_y) + cursor_size - 10),
                         (int(cursor_x), int(cursor_y) + cursor_size + 5), 3)

        # Draw exit hint (small, for parents)
        hint_text = small_font.render("Press ESC to exit | Controller: Left Stick + A Button", True, (100, 100, 100))
        screen.blit(hint_text, (SCREEN_WIDTH - 380, SCREEN_HEIGHT - 30))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
