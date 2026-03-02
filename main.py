import pygame
import numpy as np
import sounddevice as sd

WIDTH, HEIGHT = 800, 600
TARGET_POS = np.array([600, 300])
PLAYER_POS = np.array([100, 300])
MAX_DIST = 600
SAMPLE_RATE = 44100

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sound Fairy Game (Skeleton)")
clock = pygame.time.Clock()


def generate_tone(freq=440, duration=0.2):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tone = np.sin(freq * t * 2 * np.pi)
    return tone.astype(np.float32)


base_sound = generate_tone()


def make_stereo(sound, left, right):
    return np.column_stack((sound * left, sound * right))


running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        PLAYER_POS[0] -= 5
    if keys[pygame.K_RIGHT]:
        PLAYER_POS[0] += 5
    if keys[pygame.K_UP]:
        PLAYER_POS[1] -= 5
    if keys[pygame.K_DOWN]:
        PLAYER_POS[1] += 5

    PLAYER_POS[0] = np.clip(PLAYER_POS[0], 0, WIDTH)
    PLAYER_POS[1] = np.clip(PLAYER_POS[1], 0, HEIGHT)

    diff = TARGET_POS - PLAYER_POS
    dist = np.linalg.norm(diff)
    volume = max(0.0, 1.0 - dist / MAX_DIST)

    pan = diff[0] / MAX_DIST
    pan = np.clip(pan, -1, 1)

    left = volume * (1 - pan) / 2
    right = volume * (1 + pan) / 2

    stereo_sound = make_stereo(base_sound, left, right)
    sd.play(stereo_sound, SAMPLE_RATE, blocking=False)

    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (0, 255, 0), PLAYER_POS.astype(int), 5)
    pygame.display.flip()

pygame.quit()
