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
def bold_font(size):
    key = f"bold_{size}"
    if key not in font_cache:
        font_cache[key] = pygame.font.Font("bold_font_8.ttf", size)
    return font_cache[key]

def font(size):
    return pygame.font.Font("PixelOperator.ttf", size)


def gifframes(path, size):
    frames = []
    try:
        gif = pygame.image.load(path)
        gif = pygame.transform.scale(gif, size)
        frames.append(gif)
    except:
        import PIL.Image
        gif = PIL.Image.open(path)
        for frame in range(gif.n_frames):
            gif.seek(frame)
            frame_surface = pygame.image.fromstring(gif.tobytes(), gif.size, gif.mode).convert_alpha()
            frame_surface = pygame.transform.scale(frame_surface, size)
            frames.append(frame_surface)
    return frames

gif_frames = gifframes("enemy_sprite.gif", (100, 100))
gif_frame_duration = 100
gif_state = {
    "current_frame": 0,
    "last_update": pygame.time.get_ticks()
}

def update_gif():
    now = pygame.time.get_ticks()
    if now - gif_state["last_update"] >= gif_frame_duration:
        gif_state["current_frame"] = (gif_state["current_frame"] + 1) % len(gif_frames)
        gif_state["last_update"] = now
    return gif_frames[gif_state["current_frame"]]

battleost = mixer.Sound("spider_dance.mp3")
strikedsfx = mixer.Sound("strike.mp3")
shattersfx = mixer.Sound("soul_shatter.mp3")
gameoverost = mixer.Sound("game_over.mp3")

mixer.Channel(1).play(battleost, loops=-1)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

BOX_SIZE = 250
box = pygame.Rect((WIDTH - BOX_SIZE) // 2, (HEIGHT - BOX_SIZE) // 2 + 50, BOX_SIZE, BOX_SIZE)

playersize = 20
player_x, player_y = box.center
hp = maxhealth = 2
level = 1

arrow_count = 3
arrow_cooldown = 1500
last_swarm_time = flash_time = 0

WAITING, FLASHING, SPAWNING, MOVING, PAUSING, INTERMISSION = range(6)
current_state = WAITING

arrow_width, arrow_height = 15, 60
arrowimg = pygame.transform.scale(pygame.image.load("arrow.png").convert_alpha(), (arrow_width, arrow_height))
pointerimg = pygame.transform.scale(pygame.image.load("pointer.png").convert_alpha(), (30, 30))
heartimg = pygame.transform.scale(pygame.image.load("heart.png").convert_alpha(), (playersize, playersize))
clock = pygame.time.Clock()

def health_bar():
    bar_w, bar_h = 100, 15
    y = box.bottom + 10
    lvl_s = bold_font(24).render(f"LVL {level}", True, WHITE)
    hp_s = bold_font(24).render("HP", True, WHITE)
    space1, space2 = 20, 10
    total_w = lvl_s.get_width() + space1 + hp_s.get_width() + space2 + bar_w
    x = (WIDTH - total_w) // 2
    screen.blit(lvl_s, (x, y))
    screen.blit(hp_s, (x + lvl_s.get_width() + space1, y))
    bar_x = x + lvl_s.get_width() + space1 + hp_s.get_width() + space2
    pygame.draw.rect(screen, RED, (bar_x, y, bar_w, bar_h))
    pygame.draw.rect(screen, YELLOW, (bar_x, y, bar_w * (hp / maxhealth), bar_h))

def buttons():
    start_x = (WIDTH - 4*100 - 3*10) // 2
    for i, name in enumerate(["ATTACK","ACT","ITEM","MERCY"]):
        btn = pygame.Rect(start_x + i*110, HEIGHT - 80, 100, 50)
        pygame.draw.rect(screen, BLACK, btn)
        pygame.draw.rect(screen, (255,165,0), btn, 3)
        icon_x, icon_y = btn.x+8, btn.centery
        if current_state == INTERMISSION and i == selected_idx:
            screen.blit(heartimg, (icon_x-5, icon_y-10))
        else:
            if name == "ATTACK":
                pygame.draw.line(screen, (255,165,0), (icon_x,icon_y), (icon_x+15,icon_y), 3)
            elif name == "ACT":
                pygame.draw.circle(screen, (255,165,0), (icon_x+10,icon_y), 10, 3)
            elif name == "ITEM":
                pygame.draw.polygon(screen, (255,165,0), [(icon_x,icon_y-10),(icon_x+20,icon_y-10),(icon_x+10,icon_y+10)])
            else:
                pygame.draw.line(screen, (255,165,0), (icon_x,icon_y-15), (icon_x+30,icon_y+15), 3)
                pygame.draw.line(screen, (255,165,0), (icon_x+30,icon_y-15), (icon_x,icon_y+15), 3)
        for size in range(24,5,-1):
            txt = bold_font(size).render(name, True, (255,165,0))
            padding = 5
            symbol_space = 20
            if (txt.get_width() + symbol_space + padding*2) <= btn.width and (txt.get_height() + padding*2) <= btn.height:
                screen.blit(txt, (btn.centerx - txt.get_width()//2, btn.centery - txt.get_height()//2))
                break

def pointer_arrows(swarm):
    for rect, d in swarm:
        if d == "top":
            img = pygame.transform.rotate(pointerimg, 180); pos=(rect.x+arrow_width//2-15, box.top-30)
        elif d == "bottom":
            img = pointerimg; pos=(rect.x+arrow_width//2-15, box.bottom+10)
        elif d == "left":
            img = pygame.transform.rotate(pointerimg, -90); pos=(box.left-30, rect.y+arrow_width//2-15)
        else: img = pygame.transform.rotate(pointerimg, 90); pos=(box.right+10, rect.y+arrow_width//2-15)
        screen.blit(img, pos)

def spawn_arrows(direction, count):
    swarm = []
    for i in range(count):
        if direction == "top":
            x = box.left + random.randint(0, BOX_SIZE-arrow_width)
            y = box.top + i*(arrow_height//2)
        elif direction == "bottom":
            x = box.left + random.randint(0, BOX_SIZE-arrow_width)
            y = box.bottom - arrow_height - i*(arrow_height//2)
        elif direction == "left":
            x = box.left + i*(arrow_height//2)
            y = box.top + random.randint(0, BOX_SIZE-arrow_width)
        else:  # right
            x = box.right - arrow_width - i*(arrow_height//2)
            y = box.top + random.randint(0, BOX_SIZE-arrow_width)
        swarm.append((pygame.Rect(x, y, arrow_width, arrow_height), direction))
    return swarm

def arrow_swarm():
    for rect, d in arrows_list:
        img = arrowimg
        if d == "left":
            img = pygame.transform.rotate(arrowimg, -90)
        elif d == "right":
            img = pygame.transform.rotate(arrowimg, 90)
        elif d == "top":
            img = pygame.transform.rotate(arrowimg, 180)
        elif d == "bottom":
            img = arrowimg
        screen.blit(img, rect.topleft)

background = pygame.Surface((WIDTH, HEIGHT))
background.fill((0, 0, 0))
pygame.draw.rect(background, (200, 200, 200), pygame.Rect((WIDTH - 250) // 2, (HEIGHT - 250) // 2 + 50, 250, 250), 3)

def game():
    global radar_on, selected_idx, player_x, player_y, arrows_list, score, hp, arrow_cooldown, first_swarm
    global current_state, pending_swarm, flash_arrow, last_swarm_time, flash_time, arrow_count
    
    radar_on = True
    selected_idx = 0
    arrows_list = []
    score = 0
    hp = maxhealth = 2
    player_x, player_y = box.center
    arrow_count = 3
    arrow_cooldown = 1500
    last_swarm_time = flash_time = 0
    first_swarm = True
    current_state = 0
    pending_swarm = []
    flash_arrow = None
    game_over = False
    pause_start = 0
    
    while True:
        screen.blit(heartimg, (player_x, player_y))
        health_bar()
        buttons()
        
        now = pygame.time.get_ticks()

        screen.blit(background, (0, 0))
        gif_img = update_gif()
        gif_rect = gif_img.get_rect(center=((WIDTH // 2), ((HEIGHT - 250) // 2 + 50) - 60))
        screen.blit(gif_img, gif_rect)
        screen.blit(heartimg, (player_x, player_y))
        health_bar()
        buttons()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_x:
                radar_on = not radar_on
                if not radar_on and current_state == INTERMISSION:
                    current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()
            if game_over and e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                mixer.Channel(3).stop()
                mixer.Channel(1).play(battleost, loops=-1)
                return
            if current_state == INTERMISSION and e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_a, pygame.K_LEFT): selected_idx = (selected_idx-1) % 4
                if e.key in (pygame.K_d, pygame.K_RIGHT): selected_idx = (selected_idx+1) % 4
                if e.key in (pygame.K_z, pygame.K_RETURN):
                    current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()
        if not game_over and current_state != INTERMISSION:
            keys = pygame.key.get_pressed()
            speed = 5.7 + (6.2 - 5.7) * min(score, 30) / 30
            if keys[pygame.K_LEFT] and player_x > box.left: player_x -= speed
            if keys[pygame.K_RIGHT] and player_x < box.right - playersize: player_x += speed
            if keys[pygame.K_UP] and player_y > box.top: player_y -= speed
            if keys[pygame.K_DOWN] and player_y < box.bottom - playersize: player_y += speed
            if current_state == WAITING and now - last_swarm_time >= arrow_cooldown:
                if first_swarm:
                    direction = "bottom"
                    first_swarm = False
                else:
                    direction = random.choice(["top", "left", "right"]);
                current_state = FLASHING
                flash_arrow = direction
                pending_swarm = spawn_arrows(direction, arrow_count)
                flash_time = now
        if not game_over and current_state == FLASHING and now - flash_time < 700:
            pointer_arrows(pending_swarm)
        if not game_over and current_state == FLASHING and now - flash_time >= 700:
            current_state = SPAWNING
        if not game_over and current_state == SPAWNING:
            arrows_list += pending_swarm
            pending_swarm = []
            last_swarm_time = now
            current_state = MOVING
        if not game_over and current_state == MOVING:
            for rect, d in arrows_list[:]:
                if d == "top": rect.y += 8
                elif d == "left": rect.x += 8
                elif d == "right": rect.x -= 8
                elif d == "bottom": rect.y -= 8
                if not box.colliderect(rect):
                    arrows_list.remove((rect, d)); continue
                if rect.colliderect(pygame.Rect(player_x, player_y, playersize, playersize)):
                    hp -= 1; mixer.Channel(2).play(strikedsfx); arrows_list.remove((rect, d))
                    if hp <= 0:
                        mixer.Channel(1).stop(); mixer.Channel(2).stop(); ch = pygame.mixer.Channel(3)
                        ch.play(shattersfx); ch.queue(gameoverost); game_over = True
                heart_rect = pygame.Rect(player_x + 4, player_y + 4, playersize - 8, playersize - 8)
                arrow_hitbox = rect.copy()
                if d in ["left", "right"]: arrow_hitbox.inflate_ip(-6, 0)
                if arrow_hitbox.colliderect(heart_rect):
                    hp -= 1
                    mixer.Channel(2).play(strikedsfx)
                    arrows_list.remove((rect, d))
                    if hp <= 0:
                        mixer.Channel(1).stop()
                        mixer.Channel(2).stop()
                        ch = pygame.mixer.Channel(3)
                        ch.play(shattersfx)
                        ch.queue(gameoverost)
                        game_over = True
                arrow_swarm()
        if not game_over and current_state == MOVING and not arrows_list:
            score += 1; arrow_count = 6 if score >= 40 else 5 if score >= 20 else 3 + score // 20
            arrow_cooldown = max(300, 1500 - score * 60)
            current_state, pause_start = PAUSING, now
        if not game_over and current_state == PAUSING and now - pause_start >= 700 * (1 - min(score, 30) / 30):
            current_state = INTERMISSION if radar_on else WAITING
            if current_state == WAITING: last_swarm_time = now

        if game_over:
            screen.fill(BLACK)
            go = bold_font(48).render("GAME OVER", True, RED)
            screen.blit(go, go.get_rect(center=(WIDTH//2, HEIGHT//2-60)))
            sc = font(24).render(f"Score: {score}", True, WHITE)
            screen.blit(sc, sc.get_rect(center=(WIDTH//2, HEIGHT//2)))
            pr = font(24).render("Press SPACE to restart", True, WHITE)
            screen.blit(pr, pr.get_rect(center=(WIDTH//2, HEIGHT//2+60)))

        pygame.display.flip()
        clock.tick(60)

while True:
    game()
