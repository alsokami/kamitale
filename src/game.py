import pygame
from pygame import mixer
import random
import sys

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 650, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("kamitale")

font_cache = {}
def get_bold_pixel_font(size):
    key = f"bold_{size}"
    if key not in font_cache:
        font_cache[key] = pygame.font.Font("bold_font_8.ttf", size)
    return font_cache[key]

def get_pixel_font(size):
    return pygame.font.Font("PixelOperator.ttf", size)

battle_sound = mixer.Sound("spider_dance.mp3")
strike_sound = mixer.Sound("strike.mp3")
shatter_sound = mixer.Sound("soul_shatter.mp3")
gameover_sound = mixer.Sound("game_over.mp3")

mixer.Channel(1).play(battle_sound, loops=-1)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

BOX_SIZE = 250
box_rect = pygame.Rect((WIDTH - BOX_SIZE) // 2, (HEIGHT - BOX_SIZE) // 2 + 50, BOX_SIZE, BOX_SIZE)

player_size = 20
player_x, player_y = box_rect.center
player_hp = player_max_hp = 2
level = 1

arrow_count = 3
arrow_cooldown = 1500
last_swarm_time = flash_time = 0

WAITING, FLASHING, SPAWNING, MOVING, PAUSING, INTERMISSION = range(6)
current_state = WAITING

arrow_width, arrow_height = 15, 60
arrow_image = pygame.image.load("arrow.png").convert_alpha()
arrow_image = pygame.transform.scale(arrow_image, (arrow_width, arrow_height))

pointer_image = pygame.image.load("pointer.png").convert_alpha()
pointer_image = pygame.transform.scale(pointer_image, (30, 30))

heart_image = pygame.image.load("heart.png").convert_alpha()
heart_image = pygame.transform.scale(heart_image, (player_size, player_size))

clock = pygame.time.Clock()

def spawn_arrows(direction, count):
    swarm = []
    for i in range(count):
        if direction == "top":
            x = box_rect.left + random.randint(0, BOX_SIZE - arrow_width)
            y = box_rect.top + i * (arrow_height // 2)
        elif direction == "left":
            x = box_rect.left + i * (arrow_height // 2)
            y = box_rect.top + random.randint(0, BOX_SIZE - arrow_width)
        else:
            x = box_rect.right - arrow_width - i * (arrow_height // 2)
            y = box_rect.top + random.randint(0, BOX_SIZE - arrow_width)
        swarm.append((pygame.Rect(x, y, arrow_width, arrow_height), direction))
    return swarm

def draw_health_bar():
    bar_w, bar_h = 100, 15
    y = box_rect.bottom + 10
    lvl_s = get_bold_pixel_font(24).render(f"LVL {level}", True, WHITE)
    hp_s = get_bold_pixel_font(24).render("HP", True, WHITE)
    space1, space2 = 20, 10
    total_w = lvl_s.get_width() + space1 + hp_s.get_width() + space2 + bar_w
    x = (WIDTH - total_w) // 2
    screen.blit(lvl_s, (x, y))
    screen.blit(hp_s, (x + lvl_s.get_width() + space1, y))
    bar_x = x + lvl_s.get_width() + space1 + hp_s.get_width() + space2
    pygame.draw.rect(screen, RED, (bar_x, y, bar_w, bar_h))
    pygame.draw.rect(screen, YELLOW, (bar_x, y, bar_w * (player_hp / player_max_hp), bar_h))

def draw_radar():
    cx, cy = box_rect.centerx, box_rect.top - 30
    color = RED if radar_on else (0,255,0)
    pygame.draw.circle(screen, color, (cx, cy), 10)
    label = get_bold_pixel_font(12).render("IGNORE INTERMISSION", True, WHITE)
    screen.blit(label, (cx - label.get_width()//2, cy + 15))

def draw_buttons():
    start_x = (WIDTH - 4*100 - 3*10) // 2
    for i, name in enumerate(["ATTACK","ACT","ITEM","MERCY"]):
        btn = pygame.Rect(start_x + i*110, HEIGHT - 80, 100, 50)
        pygame.draw.rect(screen, BLACK, btn)
        pygame.draw.rect(screen, (255,165,0), btn, 3)
        icon_x, icon_y = btn.x+8, btn.centery
        if current_state == INTERMISSION and i == selected_idx:
            screen.blit(heart_image, (icon_x-5, icon_y-10))
        else:
            if name=="ATTACK": pygame.draw.line(screen,(255,165,0),(icon_x,icon_y),(icon_x+15,icon_y),3)
            elif name=="ACT": pygame.draw.circle(screen,(255,165,0),(icon_x+10,icon_y),10,3)
            elif name=="ITEM": pygame.draw.polygon(screen,(255,165,0),[(icon_x,icon_y-10),(icon_x+20,icon_y-10),(icon_x+10,icon_y+10)])
            else:
                pygame.draw.line(screen,(255,165,0),(icon_x,icon_y-15),(icon_x+30,icon_y+15),3)
                pygame.draw.line(screen,(255,165,0),(icon_x+30,icon_y-15),(icon_x,icon_y+15),3)
        text = get_bold_pixel_font(16).render(name, True, (255,165,0))
        screen.blit(text, (btn.x+40, btn.centery - text.get_height()//2))

def draw_pointers(swarm):
    for rect, d in swarm:
        if d == "top":
            img = pygame.transform.rotate(pointer_image, 180)
            pos = (rect.x + arrow_width//2 - 15, box_rect.top - 30)
        elif d == "left":
            img = pygame.transform.rotate(pointer_image, -90)
            pos = (box_rect.left - 30, rect.y + arrow_width//2 - 15)
        else:
            img = pygame.transform.rotate(pointer_image, 90)
            pos = (box_rect.right + 10, rect.y + arrow_width//2 - 15)
        screen.blit(img, pos)

def draw_arrows():
    for rect, d in arrows_list:
        img = arrow_image
        if d == "left": img = pygame.transform.rotate(arrow_image, -90)
        elif d == "right": img = pygame.transform.rotate(arrow_image, 90)
        elif d == "top": img = pygame.transform.rotate(arrow_image, 180)
        screen.blit(img, rect.topleft)

def game_loop():
    global radar_on, selected_idx, player_x, player_y, arrows_list, score, player_hp, arrow_cooldown
    global current_state, pending_swarm, flash_arrow, last_swarm_time, flash_time, arrow_count
    radar_on, selected_idx = True, 0
    pending_swarm, flash_arrow = [], None
    player_x, player_y = box_rect.center
    arrows_list, score, player_hp, arrow_count = [], 0, player_max_hp, 3
    current_state, last_swarm_time = WAITING, pygame.time.get_ticks()
    game_over = False

    while True:
        screen.fill(BLACK)
        pygame.draw.rect(screen, GRAY, box_rect, 3)
        draw_radar()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_x:
                radar_on = not radar_on
                if not radar_on and current_state == INTERMISSION:
                    current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()
            if game_over and e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                return
            if current_state == INTERMISSION and e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_a, pygame.K_LEFT): selected_idx = (selected_idx-1)%4
                if e.key in (pygame.K_d, pygame.K_RIGHT): selected_idx = (selected_idx+1)%4
                if e.key in (pygame.K_z, pygame.K_RETURN):
                    current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()

        now = pygame.time.get_ticks()
        if not game_over and current_state != INTERMISSION:
            keys = pygame.key.get_pressed()
            speed = 5.7 + (6.2 - 5.7) * min(score, 30) / 30
            if keys[pygame.K_LEFT] and player_x > box_rect.left: player_x -= speed
            if keys[pygame.K_RIGHT] and player_x < box_rect.right - player_size: player_x += speed
            if keys[pygame.K_UP] and player_y > box_rect.top: player_y -= speed
            if keys[pygame.K_DOWN] and player_y < box_rect.bottom - player_size: player_y += speed

        if not game_over:
            if current_state == WAITING and now - last_swarm_time >= arrow_cooldown:
                current_state, flash_arrow, pending_swarm, flash_time = FLASHING, random.choice(["top","left","right"]), spawn_arrows(flash_arrow, arrow_count), now
            if current_state == FLASHING and now - flash_time < 700:
                draw_pointers(pending_swarm)
            if current_state == FLASHING and now - flash_time >= 700:
                current_state = SPAWNING
            if current_state == SPAWNING:
                arrows_list += pending_swarm; pending_swarm = []
                last_swarm_time = now; current_state = MOVING
            if current_state == MOVING:
                for rect, d in arrows_list[:]:
                    if d == "top": rect.y += 8
                    elif d == "left": rect.x += 8
                    else: rect.x -= 8
                    if not box_rect.colliderect(rect): arrows_list.remove((rect,d)); continue
                    if rect.colliderect(pygame.Rect(player_x,player_y,player_size,player_size)):
                        player_hp -= 1; mixer.Channel(2).play(strike_sound); arrows_list.remove((rect,d))
                        if player_hp <= 0:
                            mixer.Channel(1).stop(); mixer.Channel(2).stop(); ch = pygame.mixer.Channel(3)
                            ch.play(shatter_sound); ch.queue(gameover_sound); game_over = True
                draw_arrows()
            if current_state == MOVING and not arrows_list:
                score += 1; arrow_count = 6 if score >= 40 else 5 if score >= 20 else 3 + score//20
                arrow_cooldown = max(300, 1500 - score * 60)
                current_state, pause_start = PAUSING, now
            if current_state == PAUSING and now - pause_start >= 700 * (1 - min(score,30)/30):
                current_state = INTERMISSION if radar_on else WAITING
                if current_state == WAITING: last_swarm_time = now

        screen.blit(heart_image,(player_x,player_y))
        draw_health_bar()
        draw_buttons()

        if game_over:
            screen.fill(BLACK)
            go = get_bold_pixel_font(48).render("GAME OVER", True, RED)
            screen.blit(go, go.get_rect(center=(WIDTH//2,HEIGHT//2-60)))
            sc = get_pixel_font(24).render(f"Score: {score}", True, WHITE)
            screen.blit(sc, sc.get_rect(center=(WIDTH//2,HEIGHT//2)))
            pr = get_pixel_font(24).render("Press SPACE to restart", True, WHITE)
            screen.blit(pr, pr.get_rect(center=(WIDTH//2,HEIGHT//2+60)))

        pygame.display.flip()
        clock.tick(60)

while True:
    game_loop()

