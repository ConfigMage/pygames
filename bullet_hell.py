"""
NOVA STORM - A Bullet Hell Shooter
Intense action, beautiful patterns, satisfying gameplay.
For teens and adults who want a challenge!
"""

import pygame
import random
import math
import sys
from enum import Enum
from dataclasses import dataclass

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.joystick.init()

# Screen setup
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("NOVA STORM")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 80, 80)
ORANGE = (255, 160, 60)
YELLOW = (255, 230, 80)
GREEN = (80, 255, 120)
CYAN = (80, 230, 255)
BLUE = (80, 120, 255)
PURPLE = (180, 80, 255)
PINK = (255, 80, 180)
MAGENTA = (255, 50, 255)

# Game constants
PLAYER_SPEED = 6
PLAYER_FOCUS_SPEED = 2.5
BULLET_SPEED = 12
GRAZE_DISTANCE = 25
GRAZE_POINTS = 50
INVINCIBILITY_FRAMES = 180

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    BOSS_WARNING = 5
    VICTORY = 6

# ============== PARTICLE SYSTEM ==============

class Particle:
    def __init__(self, x, y, color, vel_x=0, vel_y=0, size=3, life=30, gravity=0, fade=True):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.size = size
        self.max_life = life
        self.life = life
        self.gravity = gravity
        self.fade = fade

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += self.gravity
        self.life -= 1
        if self.fade:
            self.size = max(0.5, self.size * 0.95)

    def draw(self, surface):
        if self.life > 0:
            alpha = self.life / self.max_life
            color = tuple(int(c * alpha) for c in self.color)
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add(self, particle):
        self.particles.append(particle)

    def explosion(self, x, y, color, count=20, speed=5, size=4, life=25):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1, speed)
            self.add(Particle(
                x, y, color,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                random.uniform(2, size),
                random.randint(15, life),
                gravity=0.1
            ))

    def spark(self, x, y, color, direction=None, count=5):
        for _ in range(count):
            if direction is None:
                angle = random.uniform(0, 2 * math.pi)
            else:
                angle = direction + random.uniform(-0.5, 0.5)
            spd = random.uniform(2, 6)
            self.add(Particle(
                x, y, color,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                random.uniform(1, 3),
                random.randint(10, 20)
            ))

    def trail(self, x, y, color, size=3):
        self.add(Particle(
            x + random.uniform(-3, 3),
            y + random.uniform(-3, 3),
            color, 0, random.uniform(1, 3),
            size, random.randint(15, 25)
        ))

    def update(self):
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

# ============== BULLETS ==============

class Bullet:
    def __init__(self, x, y, vel_x, vel_y, color, radius=4, damage=1, is_player=False):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.radius = radius
        self.damage = damage
        self.is_player = is_player
        self.grazed = False
        self.trail_timer = 0

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.trail_timer += 1

    def draw(self, surface):
        # Glow effect
        glow_surf = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
        for i in range(3):
            alpha = 60 - i * 20
            r = self.radius * (3 - i)
            color = (*self.color, alpha)
            pygame.draw.circle(glow_surf, color, (self.radius * 3, self.radius * 3), r)
        surface.blit(glow_surf, (int(self.x - self.radius * 3), int(self.y - self.radius * 3)), special_flags=pygame.BLEND_ADD)

        # Core
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius // 2)

    def is_off_screen(self):
        margin = 50
        return (self.x < -margin or self.x > SCREEN_WIDTH + margin or
                self.y < -margin or self.y > SCREEN_HEIGHT + margin)

# ============== PLAYER ==============

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 150
        self.hitbox_radius = 3  # Tiny hitbox for bullet hell
        self.graze_radius = GRAZE_DISTANCE
        self.speed = PLAYER_SPEED
        self.focused = False
        self.shoot_timer = 0
        self.shoot_delay = 5
        self.power = 1.0  # 1.0 to 4.0
        self.lives = 3
        self.bombs = 3
        self.invincible = 0
        self.dead = False
        self.respawn_timer = 0

        # Visual
        self.trail_positions = []
        self.angle = 0

    def update(self, dx, dy, focused, particles):
        if self.dead:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawn()
            return

        self.focused = focused
        speed = PLAYER_FOCUS_SPEED if focused else PLAYER_SPEED

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.x += dx * speed
        self.y += dy * speed

        # Keep on screen
        margin = 20
        self.x = max(margin, min(SCREEN_WIDTH - margin, self.x))
        self.y = max(margin, min(SCREEN_HEIGHT - margin, self.y))

        # Trail
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > 10:
            self.trail_positions.pop(0)

        # Engine particles
        if random.random() < 0.3:
            particles.trail(self.x, self.y + 20, CYAN, 2)

        # Invincibility countdown
        if self.invincible > 0:
            self.invincible -= 1

        self.shoot_timer += 1
        self.angle += 0.1

    def shoot(self):
        if self.dead:
            return []

        bullets = []
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0

            # Base shot
            bullets.append(Bullet(self.x, self.y - 20, 0, -BULLET_SPEED, CYAN, 5, 1, True))

            # Power level shots
            if self.power >= 1.5:
                bullets.append(Bullet(self.x - 15, self.y - 10, -0.5, -BULLET_SPEED, CYAN, 4, 1, True))
                bullets.append(Bullet(self.x + 15, self.y - 10, 0.5, -BULLET_SPEED, CYAN, 4, 1, True))

            if self.power >= 2.5:
                bullets.append(Bullet(self.x - 30, self.y, -1, -BULLET_SPEED * 0.9, GREEN, 4, 1, True))
                bullets.append(Bullet(self.x + 30, self.y, 1, -BULLET_SPEED * 0.9, GREEN, 4, 1, True))

            if self.power >= 3.5:
                bullets.append(Bullet(self.x - 10, self.y - 15, 0, -BULLET_SPEED * 1.1, YELLOW, 3, 1, True))
                bullets.append(Bullet(self.x + 10, self.y - 15, 0, -BULLET_SPEED * 1.1, YELLOW, 3, 1, True))

        return bullets

    def hit(self, particles):
        if self.invincible > 0 or self.dead:
            return False

        self.lives -= 1
        particles.explosion(self.x, self.y, RED, 40, 8, 6, 40)
        particles.explosion(self.x, self.y, ORANGE, 30, 6, 5, 35)

        if self.lives <= 0:
            self.dead = True
            return True

        self.dead = True
        self.respawn_timer = 120
        self.power = max(1.0, self.power - 0.5)
        return False

    def respawn(self):
        self.dead = False
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 150
        self.invincible = INVINCIBILITY_FRAMES

    def bomb(self, enemy_bullets, particles):
        if self.bombs > 0 and not self.dead:
            self.bombs -= 1
            self.invincible = 120

            # Clear bullets with explosion
            for bullet in enemy_bullets:
                particles.explosion(bullet.x, bullet.y, bullet.color, 5, 3, 3, 15)
            enemy_bullets.clear()

            # Screen flash effect
            return True
        return False

    def draw(self, surface):
        if self.dead:
            return

        # Flicker when invincible
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            return

        # Trail
        for i, (tx, ty) in enumerate(self.trail_positions):
            alpha = i / len(self.trail_positions)
            size = int(3 + alpha * 5)
            color = (int(80 * alpha), int(230 * alpha), int(255 * alpha))
            pygame.draw.circle(surface, color, (int(tx), int(ty)), size)

        # Ship body
        ship_points = [
            (self.x, self.y - 25),
            (self.x - 20, self.y + 15),
            (self.x - 8, self.y + 5),
            (self.x, self.y + 20),
            (self.x + 8, self.y + 5),
            (self.x + 20, self.y + 15),
        ]
        pygame.draw.polygon(surface, CYAN, ship_points)
        pygame.draw.polygon(surface, WHITE, ship_points, 2)

        # Cockpit
        pygame.draw.ellipse(surface, (150, 220, 255), (self.x - 6, self.y - 10, 12, 15))

        # Engine glow
        glow_size = 8 + math.sin(self.angle * 2) * 2
        pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y + 18)), int(glow_size))
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y + 18)), int(glow_size * 0.5))

        # Focus mode hitbox indicator
        if self.focused:
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.hitbox_radius + 2, 1)
            pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.hitbox_radius)

            # Graze circle
            pygame.draw.circle(surface, (50, 50, 80), (int(self.x), int(self.y)), self.graze_radius, 1)

# ============== ENEMIES ==============

class Enemy:
    def __init__(self, x, y, health, points, color):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.points = points
        self.color = color
        self.time = 0
        self.shoot_timer = 0
        self.hit_flash = 0

    def update(self):
        self.time += 1
        self.shoot_timer += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def shoot(self):
        return []

    def hit(self, damage, particles):
        self.health -= damage
        self.hit_flash = 5
        particles.spark(self.x, self.y, self.color)
        return self.health <= 0

    def draw(self, surface):
        pass

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 100

class BasicEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 10, 100, PURPLE)
        self.vel_y = 2
        self.amplitude = random.uniform(50, 100)
        self.frequency = random.uniform(0.02, 0.04)
        self.start_x = x

    def update(self):
        super().update()
        self.y += self.vel_y
        self.x = self.start_x + math.sin(self.time * self.frequency) * self.amplitude

    def shoot(self):
        bullets = []
        if self.shoot_timer >= 60:
            self.shoot_timer = 0
            # Aimed shot at player
            bullets.append(Bullet(self.x, self.y, 0, 4, MAGENTA, 6))
        return bullets

    def draw(self, surface):
        color = WHITE if self.hit_flash > 0 else self.color
        # Diamond shape
        points = [
            (self.x, self.y - 20),
            (self.x + 15, self.y),
            (self.x, self.y + 20),
            (self.x - 15, self.y),
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

class SpiralEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 25, 250, ORANGE)
        self.target_y = random.randint(100, 300)
        self.angle = 0

    def update(self):
        super().update()
        # Move to position then hover
        if self.y < self.target_y:
            self.y += 2
        self.angle += 0.05

    def shoot(self):
        bullets = []
        if self.y >= self.target_y and self.shoot_timer >= 8:
            self.shoot_timer = 0
            # Spiral pattern
            angle = self.time * 0.15
            speed = 3
            bullets.append(Bullet(
                self.x, self.y,
                math.cos(angle) * speed,
                math.sin(angle) * speed + 1,
                ORANGE, 5
            ))
        return bullets

    def draw(self, surface):
        color = WHITE if self.hit_flash > 0 else self.color
        # Spinning triangle
        for i in range(3):
            angle = self.angle + i * (2 * math.pi / 3)
            px = self.x + math.cos(angle) * 20
            py = self.y + math.sin(angle) * 20
            pygame.draw.circle(surface, color, (int(px), int(py)), 8)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 12)

class BurstEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 35, 400, PINK)
        self.target_y = random.randint(80, 200)
        self.burst_count = 0

    def update(self):
        super().update()
        if self.y < self.target_y:
            self.y += 1.5
        else:
            # Slight hover movement
            self.x += math.sin(self.time * 0.03) * 0.5

    def shoot(self):
        bullets = []
        if self.y >= self.target_y and self.shoot_timer >= 90:
            self.shoot_timer = 0
            # Circular burst
            count = 16
            for i in range(count):
                angle = (2 * math.pi * i / count) + self.burst_count * 0.2
                speed = 3.5
                bullets.append(Bullet(
                    self.x, self.y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    PINK, 6
                ))
            self.burst_count += 1
        return bullets

    def draw(self, surface):
        color = WHITE if self.hit_flash > 0 else self.color
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 22)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 22, 2)
        # Inner pattern
        for i in range(6):
            angle = self.time * 0.05 + i * math.pi / 3
            px = self.x + math.cos(angle) * 12
            py = self.y + math.sin(angle) * 12
            pygame.draw.circle(surface, WHITE, (int(px), int(py)), 4)

# ============== BOSS ==============

class Boss:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = -100
        self.target_y = 150
        self.health = 2000
        self.max_health = 2000
        self.phase = 0
        self.time = 0
        self.shoot_timer = 0
        self.hit_flash = 0
        self.entering = True
        self.patterns = [
            self.pattern_spiral,
            self.pattern_aimed_burst,
            self.pattern_wall,
            self.pattern_chaos
        ]
        self.pattern_timer = 0
        self.current_pattern = 0
        self.defeated = False

    def update(self):
        self.time += 1
        self.shoot_timer += 1
        self.pattern_timer += 1

        if self.hit_flash > 0:
            self.hit_flash -= 1

        # Enter screen
        if self.entering:
            self.y += 2
            if self.y >= self.target_y:
                self.entering = False
            return

        # Hover movement
        self.x = SCREEN_WIDTH // 2 + math.sin(self.time * 0.01) * 200
        self.y = self.target_y + math.sin(self.time * 0.02) * 30

        # Phase transitions
        health_percent = self.health / self.max_health
        if health_percent < 0.25:
            self.phase = 3
        elif health_percent < 0.5:
            self.phase = 2
        elif health_percent < 0.75:
            self.phase = 1
        else:
            self.phase = 0

        # Switch patterns periodically
        if self.pattern_timer > 300:
            self.pattern_timer = 0
            self.current_pattern = (self.current_pattern + 1) % len(self.patterns)

    def shoot(self, player_x, player_y):
        if self.entering or self.defeated:
            return []

        return self.patterns[self.current_pattern](player_x, player_y)

    def pattern_spiral(self, px, py):
        bullets = []
        if self.shoot_timer >= 3:
            self.shoot_timer = 0
            arms = 4 + self.phase
            for i in range(arms):
                angle = self.time * 0.08 + (2 * math.pi * i / arms)
                speed = 3 + self.phase * 0.5
                bullets.append(Bullet(
                    self.x, self.y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    MAGENTA, 6
                ))
        return bullets

    def pattern_aimed_burst(self, px, py):
        bullets = []
        if self.shoot_timer >= 30 - self.phase * 5:
            self.shoot_timer = 0
            # Aim at player
            dx = px - self.x
            dy = py - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                dx /= dist
                dy /= dist

            count = 8 + self.phase * 4
            spread = 0.8 + self.phase * 0.2
            for i in range(count):
                offset = (i - count/2) * spread / count
                angle = math.atan2(dy, dx) + offset
                speed = 4 + self.phase * 0.5
                bullets.append(Bullet(
                    self.x, self.y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    RED, 7
                ))
        return bullets

    def pattern_wall(self, px, py):
        bullets = []
        if self.shoot_timer >= 20 - self.phase * 3:
            self.shoot_timer = 0
            # Horizontal wall with gaps
            gap_pos = (self.time // 20) % 5
            for i in range(12):
                if i == gap_pos or i == gap_pos + 1:
                    continue
                x = self.x - 200 + i * 35
                bullets.append(Bullet(x, self.y + 30, 0, 3 + self.phase * 0.5, YELLOW, 8))
        return bullets

    def pattern_chaos(self, px, py):
        bullets = []
        if self.shoot_timer >= 5 - self.phase:
            self.shoot_timer = 0
            # Random chaos
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5 + self.phase)
            color = random.choice([RED, ORANGE, YELLOW, MAGENTA, PINK])
            bullets.append(Bullet(
                self.x + random.uniform(-50, 50),
                self.y + random.uniform(-20, 40),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                color, random.randint(4, 8)
            ))
        return bullets

    def hit(self, damage, particles):
        self.health -= damage
        self.hit_flash = 3
        particles.spark(self.x + random.uniform(-40, 40), self.y + random.uniform(-30, 30), WHITE)

        if self.health <= 0:
            self.defeated = True
            return True
        return False

    def draw(self, surface):
        color = WHITE if self.hit_flash > 0 else PURPLE

        # Main body
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 60)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 60, 3)

        # Core
        core_color = [RED, ORANGE, YELLOW, WHITE][self.phase]
        pygame.draw.circle(surface, core_color, (int(self.x), int(self.y)), 25)

        # Orbiting parts
        for i in range(6):
            angle = self.time * 0.03 + i * math.pi / 3
            ox = self.x + math.cos(angle) * 80
            oy = self.y + math.sin(angle) * 40
            pygame.draw.circle(surface, color, (int(ox), int(oy)), 15)
            pygame.draw.circle(surface, WHITE, (int(ox), int(oy)), 15, 2)

        # Health bar
        bar_width = 400
        bar_height = 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = 30
        health_percent = max(0, self.health / self.max_health)

        pygame.draw.rect(surface, (40, 40, 60), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(surface, (60, 20, 20), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, int(bar_width * health_percent), bar_height))

        # Phase markers
        for i in range(4):
            marker_x = bar_x + int(bar_width * (1 - i * 0.25))
            pygame.draw.line(surface, WHITE, (marker_x, bar_y - 5), (marker_x, bar_y + bar_height + 5), 2)

# ============== POWER-UPS ==============

class PowerUp:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name  # 'power', 'bomb', 'life', 'points'
        self.time = 0
        self.collected = False

        self.colors = {
            'power': RED,
            'bomb': GREEN,
            'life': PINK,
            'points': YELLOW
        }

    def update(self):
        self.time += 1
        self.y += 1.5

    def draw(self, surface):
        color = self.colors.get(self.type, WHITE)
        bob = math.sin(self.time * 0.1) * 3

        # Glow
        pygame.draw.circle(surface, (*color, 100), (int(self.x), int(self.y + bob)), 18)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y + bob)), 12)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y + bob)), 6)

        # Letter indicator
        font = pygame.font.Font(None, 20)
        letter = self.type[0].upper()
        text = font.render(letter, True, BLACK)
        surface.blit(text, (int(self.x - 5), int(self.y + bob - 7)))

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 30

# ============== STARS BACKGROUND ==============

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(1, 4)
        self.size = 1 if self.speed < 2 else (2 if self.speed < 3 else 3)
        self.brightness = min(255, int(100 + self.speed * 35))

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        color = (self.brightness, self.brightness, self.brightness)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)

# ============== SOUND EFFECTS ==============

def create_sound(freq_start, freq_end, duration, volume=0.2):
    try:
        sample_rate = 22050
        samples = int(sample_rate * duration)
        import array
        buf = array.array('h')
        for i in range(samples):
            t = i / sample_rate
            progress = t / duration
            freq = freq_start + (freq_end - freq_start) * progress
            amplitude = int(32767 * volume * (1 - progress))
            value = int(amplitude * math.sin(2 * math.pi * freq * t))
            buf.append(value)
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None

# ============== MAIN GAME ==============

def main():
    clock = pygame.time.Clock()

    # Game objects
    player = Player()
    player_bullets = []
    enemy_bullets = []
    enemies = []
    powerups = []
    particles = ParticleSystem()
    stars = [Star() for _ in range(100)]
    boss = None

    # Game state
    state = GameState.MENU
    score = 0
    graze_count = 0
    wave = 0
    wave_timer = 0
    spawn_timer = 0
    boss_spawned = False
    screen_shake = 0
    bomb_flash = 0
    boss_warning_timer = 0

    # Controller
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    # Sounds
    shoot_sound = create_sound(800, 1000, 0.05, 0.1)
    hit_sound = create_sound(300, 100, 0.1, 0.15)
    explosion_sound = create_sound(150, 50, 0.2, 0.2)
    powerup_sound = create_sound(400, 800, 0.15, 0.15)
    bomb_sound = create_sound(100, 400, 0.3, 0.25)

    # Fonts
    try:
        title_font = pygame.font.SysFont('Impact', 80)
        font = pygame.font.SysFont('Arial', 36)
        small_font = pygame.font.SysFont('Arial', 24)
    except:
        title_font = pygame.font.Font(None, 80)
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)

    pygame.mouse.set_visible(False)
    running = True

    def spawn_enemies():
        nonlocal wave
        wave += 1

        if wave % 5 == 0:  # Boss wave
            return True

        # Normal waves
        enemy_types = [BasicEnemy, SpiralEnemy, BurstEnemy]
        count = min(3 + wave // 2, 8)

        for i in range(count):
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(-200, -50)
            enemy_type = random.choices(enemy_types, weights=[50, 30, 20])[0]
            enemies.append(enemy_type(x, y))

        return False

    def reset_game():
        nonlocal player, player_bullets, enemy_bullets, enemies, powerups, boss
        nonlocal score, graze_count, wave, wave_timer, spawn_timer, boss_spawned

        player = Player()
        player_bullets = []
        enemy_bullets = []
        enemies = []
        powerups = []
        boss = None
        score = 0
        graze_count = 0
        wave = 0
        wave_timer = 0
        spawn_timer = 0
        boss_spawned = False

    while running:
        # Input
        dx, dy = 0, 0
        shooting = False
        focused = False
        bomb_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == GameState.PLAYING:
                        state = GameState.PAUSED
                    elif state == GameState.PAUSED:
                        state = GameState.PLAYING
                    elif state in [GameState.MENU, GameState.GAME_OVER, GameState.VICTORY]:
                        running = False
                elif event.key == pygame.K_RETURN or event.key == pygame.K_z:
                    if state == GameState.MENU:
                        reset_game()
                        state = GameState.PLAYING
                    elif state in [GameState.GAME_OVER, GameState.VICTORY]:
                        state = GameState.MENU
                elif event.key == pygame.K_x and state == GameState.PLAYING:
                    bomb_pressed = True

        if state == GameState.PLAYING:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += 1
            shooting = keys[pygame.K_z] or keys[pygame.K_SPACE]
            focused = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

            # Controller
            if joystick:
                axis_x = joystick.get_axis(0)
                axis_y = joystick.get_axis(1)
                if abs(axis_x) > 0.2:
                    dx += axis_x
                if abs(axis_y) > 0.2:
                    dy += axis_y

                shooting = shooting or joystick.get_button(0)
                focused = focused or joystick.get_button(4) or joystick.get_button(5)
                bomb_pressed = bomb_pressed or joystick.get_button(1)

        # Update based on state
        if state == GameState.MENU:
            for star in stars:
                star.update()

        elif state == GameState.BOSS_WARNING:
            boss_warning_timer -= 1
            for star in stars:
                star.update()
            if boss_warning_timer <= 0:
                boss = Boss()
                boss_spawned = True
                state = GameState.PLAYING

        elif state == GameState.PLAYING:
            # Update player
            player.update(dx, dy, focused, particles)

            if shooting and not player.dead:
                new_bullets = player.shoot()
                if new_bullets and shoot_sound:
                    shoot_sound.play()
                player_bullets.extend(new_bullets)

            if bomb_pressed:
                if player.bomb(enemy_bullets, particles):
                    bomb_flash = 30
                    screen_shake = 20
                    if bomb_sound:
                        bomb_sound.play()

            # Update stars
            for star in stars:
                star.update()

            # Update player bullets
            for bullet in player_bullets[:]:
                bullet.update()
                if bullet.is_off_screen():
                    player_bullets.remove(bullet)

            # Update enemy bullets + graze
            for bullet in enemy_bullets[:]:
                bullet.update()

                # Graze detection
                if not bullet.grazed and not player.dead:
                    dist = math.sqrt((bullet.x - player.x)**2 + (bullet.y - player.y)**2)
                    if dist < player.graze_radius:
                        bullet.grazed = True
                        graze_count += 1
                        score += GRAZE_POINTS
                        particles.spark(bullet.x, bullet.y, WHITE, count=3)

                if bullet.is_off_screen():
                    enemy_bullets.remove(bullet)

            # Update enemies
            for enemy in enemies[:]:
                enemy.update()
                new_bullets = enemy.shoot()
                enemy_bullets.extend(new_bullets)

                if enemy.is_off_screen():
                    enemies.remove(enemy)

            # Update boss
            if boss and not boss.defeated:
                boss.update()
                new_bullets = boss.shoot(player.x, player.y)
                enemy_bullets.extend(new_bullets)

            # Update powerups
            for powerup in powerups[:]:
                powerup.update()
                if powerup.is_off_screen():
                    powerups.remove(powerup)

            # Collision: player bullets vs enemies
            for bullet in player_bullets[:]:
                for enemy in enemies[:]:
                    dist = math.sqrt((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2)
                    if dist < 25:
                        if bullet in player_bullets:
                            player_bullets.remove(bullet)
                        if enemy.hit(bullet.damage, particles):
                            enemies.remove(enemy)
                            score += enemy.points
                            particles.explosion(enemy.x, enemy.y, enemy.color, 25, 6, 5, 30)
                            if explosion_sound:
                                explosion_sound.play()
                            # Drop powerup
                            if random.random() < 0.3:
                                ptype = random.choices(['power', 'points', 'bomb', 'life'], weights=[40, 40, 15, 5])[0]
                                powerups.append(PowerUp(enemy.x, enemy.y, ptype))
                        else:
                            if hit_sound:
                                hit_sound.play()
                        break

            # Collision: player bullets vs boss
            if boss and not boss.defeated:
                for bullet in player_bullets[:]:
                    dist = math.sqrt((bullet.x - boss.x)**2 + (bullet.y - boss.y)**2)
                    if dist < 60:
                        if bullet in player_bullets:
                            player_bullets.remove(bullet)
                        if boss.hit(bullet.damage, particles):
                            particles.explosion(boss.x, boss.y, PURPLE, 50, 10, 8, 50)
                            particles.explosion(boss.x, boss.y, WHITE, 40, 8, 6, 40)
                            screen_shake = 40
                            score += 10000
                            if explosion_sound:
                                explosion_sound.play()
                            state = GameState.VICTORY
                        else:
                            if hit_sound:
                                hit_sound.play()

            # Collision: enemy bullets vs player
            if not player.dead and player.invincible <= 0:
                for bullet in enemy_bullets[:]:
                    dist = math.sqrt((bullet.x - player.x)**2 + (bullet.y - player.y)**2)
                    if dist < player.hitbox_radius + bullet.radius:
                        enemy_bullets.remove(bullet)
                        game_over = player.hit(particles)
                        screen_shake = 25
                        if explosion_sound:
                            explosion_sound.play()
                        if game_over:
                            state = GameState.GAME_OVER
                        break

            # Collision: powerups vs player
            for powerup in powerups[:]:
                dist = math.sqrt((powerup.x - player.x)**2 + (powerup.y - player.y)**2)
                if dist < 30:
                    powerups.remove(powerup)
                    if powerup_sound:
                        powerup_sound.play()
                    if powerup.type == 'power':
                        player.power = min(4.0, player.power + 0.25)
                        score += 100
                    elif powerup.type == 'bomb':
                        player.bombs = min(5, player.bombs + 1)
                        score += 200
                    elif powerup.type == 'life':
                        player.lives = min(5, player.lives + 1)
                        score += 500
                    elif powerup.type == 'points':
                        score += 1000

            # Wave spawning
            if not boss_spawned:
                wave_timer += 1
                if len(enemies) == 0 and wave_timer > 120:
                    wave_timer = 0
                    is_boss_wave = spawn_enemies()
                    if is_boss_wave:
                        state = GameState.BOSS_WARNING
                        boss_warning_timer = 180

            # Update particles
            particles.update()

            # Screen shake decay
            if screen_shake > 0:
                screen_shake -= 1

            # Bomb flash decay
            if bomb_flash > 0:
                bomb_flash -= 1

        # Draw
        # Apply screen shake
        shake_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        shake_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

        screen.fill(BLACK)

        # Stars
        for star in stars:
            star.draw(screen)

        if state == GameState.MENU:
            # Title
            title = title_font.render("NOVA STORM", True, CYAN)
            title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
            screen.blit(title, title_rect)

            subtitle = font.render("A Bullet Hell Experience", True, WHITE)
            sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 70))
            screen.blit(subtitle, sub_rect)

            start_text = font.render("Press ENTER or Z to Start", True, YELLOW)
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(start_text, start_rect)

            controls = [
                "Arrow Keys / Left Stick - Move",
                "Z / A Button - Shoot",
                "X / B Button - Bomb",
                "Shift / LB/RB - Focus (slow + show hitbox)",
                "ESC - Pause / Exit"
            ]
            for i, line in enumerate(controls):
                text = small_font.render(line, True, (150, 150, 150))
                rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150 + i * 30))
                screen.blit(text, rect)

        elif state == GameState.BOSS_WARNING:
            # Dramatic boss warning
            flash = (boss_warning_timer // 10) % 2
            if flash:
                warning = title_font.render("WARNING", True, RED)
            else:
                warning = title_font.render("WARNING", True, ORANGE)
            rect = warning.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(warning, rect)

            boss_text = font.render("BOSS APPROACHING", True, WHITE)
            boss_rect = boss_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
            screen.blit(boss_text, boss_rect)

        elif state in [GameState.PLAYING, GameState.PAUSED]:
            # Game objects with shake offset
            offset = (shake_x, shake_y)

            # Powerups
            for powerup in powerups:
                powerup.draw(screen)

            # Enemy bullets
            for bullet in enemy_bullets:
                bullet.draw(screen)

            # Player bullets
            for bullet in player_bullets:
                bullet.draw(screen)

            # Enemies
            for enemy in enemies:
                enemy.draw(screen)

            # Boss
            if boss and not boss.defeated:
                boss.draw(screen)

            # Player
            player.draw(screen)

            # Particles
            particles.draw(screen)

            # Bomb flash
            if bomb_flash > 0:
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                alpha = int(200 * (bomb_flash / 30))
                flash_surf.fill((255, 255, 255, alpha))
                screen.blit(flash_surf, (0, 0))

            # UI
            score_text = font.render(f"SCORE: {score:,}", True, WHITE)
            screen.blit(score_text, (20, 20))

            graze_text = small_font.render(f"GRAZE: {graze_count}", True, (150, 150, 150))
            screen.blit(graze_text, (20, 60))

            # Lives
            lives_text = small_font.render(f"LIVES: {'★ ' * player.lives}", True, PINK)
            screen.blit(lives_text, (20, SCREEN_HEIGHT - 80))

            # Bombs
            bombs_text = small_font.render(f"BOMBS: {'● ' * player.bombs}", True, GREEN)
            screen.blit(bombs_text, (20, SCREEN_HEIGHT - 50))

            # Power
            power_text = small_font.render(f"POWER: {player.power:.2f}", True, RED)
            screen.blit(power_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50))

            # Wave
            wave_text = small_font.render(f"WAVE: {wave}", True, CYAN)
            screen.blit(wave_text, (SCREEN_WIDTH - 150, 20))

            if state == GameState.PAUSED:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))

                pause_text = title_font.render("PAUSED", True, WHITE)
                pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                screen.blit(pause_text, pause_rect)

        elif state == GameState.GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            go_text = title_font.render("GAME OVER", True, RED)
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(go_text, go_rect)

            final_score = font.render(f"Final Score: {score:,}", True, WHITE)
            fs_rect = final_score.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
            screen.blit(final_score, fs_rect)

            retry_text = small_font.render("Press ENTER to return to menu", True, YELLOW)
            retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
            screen.blit(retry_text, retry_rect)

        elif state == GameState.VICTORY:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 50, 180))
            screen.blit(overlay, (0, 0))

            win_text = title_font.render("VICTORY!", True, YELLOW)
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(win_text, win_rect)

            final_score = font.render(f"Final Score: {score:,}", True, WHITE)
            fs_rect = final_score.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
            screen.blit(final_score, fs_rect)

            graze_final = small_font.render(f"Total Grazes: {graze_count}", True, CYAN)
            gf_rect = graze_final.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
            screen.blit(graze_final, gf_rect)

            cont_text = small_font.render("Press ENTER to return to menu", True, WHITE)
            cont_rect = cont_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 130))
            screen.blit(cont_text, cont_rect)

        # Always show exit hint
        if state != GameState.MENU:
            hint = small_font.render("ESC to pause/exit", True, (80, 80, 80))
            screen.blit(hint, (SCREEN_WIDTH - 180, 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
