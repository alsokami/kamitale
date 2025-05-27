import pygame  # import pygame for game creation
import random  # import random for arrow spawning
import sys       # import sys for system exit

# initialize pygame
pygame.init()

# font cache
font_cache = {}
def get_bold_pixel_font(size):
    key = f"bold_{size}"
    if key not in font_cache:
        font_cache[key] = pygame.font.Font("PixelOperator8-Bold.ttf", size)
    return font_cache[key]

def get_pixel_font(size):
    return pygame.font.Font("PixelOperator.ttf", size)

# screen setup
WIDTH, HEIGHT = 650, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("kamitale")

# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (200, 200, 200)

radar_on = True    # <<< radar switch (you did have this)
selected_idx = 0
clock = pygame.time.Clock()

# game box
BOX_SIZE = 250
box_rect = pygame.Rect((WIDTH - BOX_SIZE)//2,
                       (HEIGHT - BOX_SIZE)//2 + 50,
                       BOX_SIZE, BOX_SIZE)

# player
player_size = 20
player_x = box_rect.centerx
player_y = box_rect.centery
player_speed = 6
player_hp = 2
player_max_hp = 2
level = 1

# arrows
arrow_width, arrow_height = 10, 40
pending_swarm: list[tuple[pygame.Rect, str]] = []
arrows_list: list[tuple[pygame.Rect, str]] = []
flash_arrow = None

# timing
arrow_cooldown = 1500
last_swarm_time = 0
flash_time = 0

# states
WAITING, FLASHING, SPAWNING, MOVING, PAUSING, INTERMISSION = range(6)
current_state = WAITING

# draw heart
def draw_heart(x, y):
    pygame.draw.polygon(screen, RED, [
        (x, y + 5), (x + 10, y - 5),
        (x + 20, y + 5), (x + 10, y + 20)
    ])


def draw_radar_switch():
    # draw a small circle on top of the box, centered horizontally
    radius = 10
    cx = box_rect.centerx
    cy = box_rect.top - 30  # above the box
    color = (255, 0, 0) if radar_on else GREEN  # use green if on, red if off
    pygame.draw.circle(screen, color, (cx, cy), radius)
    
    # optional: draw label below the radar
    label = get_bold_pixel_font(12).render("DO NOTHING SWITCH", True, WHITE)
    screen.blit(label, (cx - label.get_width() // 2, cy + radius + 5))

# spawn arrows
def spawn_arrows(direction, count):
    swarm = []
    for i in range(count):
        if direction == "top":
            x = box_rect.left + random.randint(0, BOX_SIZE - arrow_width)
            y = box_rect.top + i*20
            swarm.append((pygame.Rect(x, y, arrow_width, arrow_height), "top"))
        elif direction == "left":
            y = box_rect.top + random.randint(0, BOX_SIZE - arrow_height)
            x = box_rect.left + i*20
            swarm.append((pygame.Rect(x, y, arrow_height, arrow_width), "left"))
        else:
            y = box_rect.top + random.randint(0, BOX_SIZE - arrow_height)
            x = box_rect.right - arrow_width - i*20
            swarm.append((pygame.Rect(x, y, arrow_height, arrow_width), "right"))
    return swarm

# flash arrows
def draw_yellow_arrows(swarm):
    for rect, d in swarm:
        if d == "top":
            x, y = rect.x, box_rect.top - 20
            pygame.draw.polygon(screen, YELLOW, [
                (x + arrow_width//2, y + 10),
                (x + arrow_width//2 -10, y),
                (x + arrow_width//2 +10, y)
            ])
        elif d == "left":
            x, y = box_rect.left -20, rect.y
            pygame.draw.polygon(screen, YELLOW, [
                (x +10, y + arrow_width//2),
                (x, y + arrow_width//2 -10),
                (x, y + arrow_width//2 +10)
            ])
        else:
            x, y = box_rect.right +10, rect.y
            pygame.draw.polygon(screen, YELLOW, [
                (x, y + arrow_width//2),
                (x +10, y + arrow_width//2 -10),
                (x +10, y + arrow_width//2 +10)
            ])

# health bar & level (original layout)
# health bar & level (centered under the box)
def draw_health_bar():
    bar_w, bar_h = 100, 15
    y = box_rect.bottom + 10

    # render texts
    lvl_s = get_bold_pixel_font(24).render(f"LVL {level}", True, WHITE)
    hp_s  = get_bold_pixel_font(24).render("HP", True, WHITE)

    # spacing between items
    space1 = 20  # between LVL and HP
    space2 = 10  # between HP and bar

    # total width of all elements
    total_width = lvl_s.get_width() + space1 + hp_s.get_width() + space2 + bar_w

    # starting x so the whole line is centered
    x_start = (WIDTH - total_width) // 2

    # positions
    lvl_x = x_start
    hp_x = lvl_x + lvl_s.get_width() + space1
    bar_x = hp_x + hp_s.get_width() + space2

    # draw
    screen.blit(lvl_s, (lvl_x, y))
    screen.blit(hp_s,  (hp_x, y))
    pygame.draw.rect(screen, RED, (bar_x, y, bar_w, bar_h))  # red bg
    percent = player_hp / player_max_hp
    pygame.draw.rect(screen, YELLOW, (bar_x, y, bar_w * percent, bar_h))  # yellow fg


# buttons
# buttons (moved lower)
button_w, button_h, m = 100, 50, 10
button_y = HEIGHT - 80  # adjust this value to move up/down
attack_button = pygame.Rect((WIDTH - button_w*4 - m*3)//2, button_y, button_w, button_h)
act_button    = attack_button.move(button_w + m, 0)
item_button   = act_button.move(button_w + m, 0)
mercy_button  = item_button.move(button_w + m, 0)
buttons = [attack_button, act_button, item_button, mercy_button]


# draw buttons
def draw_buttons():
    icon_margin = 8
    for i, btn in enumerate(buttons):
        pygame.draw.rect(screen, BLACK, btn)
        pygame.draw.rect(screen, ORANGE, btn, 3)
        # during intermission, replace icon with heart
        icon_x = btn.x + icon_margin
        icon_y = btn.centery

        if current_state == INTERMISSION and i == selected_idx:
            # draw heart icon instead of symbol
            draw_heart(icon_x - 5, icon_y - 10)  # adjust position slightly
        else:
            # draw normal icon
            if i == 0:
                pygame.draw.line(screen, ORANGE,
                                 (icon_x, icon_y),
                                 (icon_x +15, icon_y), 3)
            elif i == 1:
                pygame.draw.circle(screen, ORANGE,
                                   (icon_x +10, icon_y), 10, 3)
            elif i == 2:
                pygame.draw.polygon(screen, ORANGE, [
                    (icon_x,    icon_y -10),
                    (icon_x+20, icon_y -10),
                    (icon_x+10, icon_y +10)
                ])
            else:
                pygame.draw.line(screen, ORANGE,
                                 (icon_x, icon_y -15),
                                 (icon_x +30, icon_y +15), 3)
                pygame.draw.line(screen, ORANGE,
                                 (icon_x +30, icon_y -15),
                                 (icon_x,     icon_y +15), 3)

        # labels
        draw_text_inside_button(["ATTACK","ACT","ITEM","MERCY"][i], btn, btn.x + icon_margin + (25 if i==0 else 30 if i<3 else 35))

# draw text inside
def draw_text_inside_button(text, btn, x):
    max_w = btn.right - x -5
    max_h = btn.height -6
    size = 24
    while size > 6:
        f = get_bold_pixel_font(size)
        s = f.render(text, True, ORANGE)
        if s.get_width() <= max_w and s.get_height() <= max_h:
            break
        size -= 1
    surf = get_bold_pixel_font(size).render(text, True, ORANGE)
    y = btn.centery - surf.get_height()//2
    screen.blit(surf, (x, y))

# add these helper functions near the top (with other helpers)
def game_loop():
    global radar_on, selected_idx
    global player_x, player_y, arrows_list, score, player_hp, level
    global current_state, pending_swarm, flash_arrow, flash_time, last_swarm_time
    global arrow_count, arrow_cooldown, game_over, pause_start_time

    def get_player_speed(score):
        start_speed = 5.7
        max_speed = 6.2
        max_round = 30
        return start_speed + (max_speed - start_speed) * min(score, max_round) / max_round

    def get_breather_duration(score):
        start_duration = 700  # milliseconds
        max_round = 30
        return start_duration * max(0, (max_round - min(score, max_round)) / max_round)

    player_x, player_y = box_rect.center
    arrows_list.clear()
    score = 0
    player_hp = player_max_hp
    arrow_count = 3
    current_state = WAITING
    last_swarm_time = pygame.time.get_ticks()
    arrow_cooldown = 1500
    selected_idx = 0
    pause_start_time = 0
    game_over = False

    while True:
        screen.fill(BLACK)
        pygame.draw.rect(screen, GRAY, box_rect, 3)
        draw_radar_switch()  # add this line

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # listen for X to toggle radar
            if e.type == pygame.KEYDOWN and e.key == pygame.K_x:
                radar_on = not radar_on  # toggle
                # if turning off, immediately skip any intermission
                if not radar_on and current_state == INTERMISSION:
                    current_state = WAITING
                    last_swarm_time = pygame.time.get_ticks()
                    pending_swarm.clear()

            if game_over and e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                return

            if current_state == INTERMISSION and e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_a, pygame.K_LEFT):
                    selected_idx = (selected_idx - 1) % 4
                if e.key in (pygame.K_d, pygame.K_RIGHT):
                    selected_idx = (selected_idx + 1) % 4
                if e.key in (pygame.K_z, pygame.K_RETURN):
                    # confirmed choice, go to next swarm
                    current_state = WAITING
                    last_swarm_time = pygame.time.get_ticks()
                    pending_swarm.clear()

        keys = pygame.key.get_pressed()
        player_speed = get_player_speed(score)

        if not game_over and current_state != INTERMISSION:
            # move player with dynamic speed
            if keys[pygame.K_LEFT] and player_x > box_rect.left:
                player_x -= player_speed
            if keys[pygame.K_RIGHT] and player_x < box_rect.right - player_size:
                player_x += player_speed
            if keys[pygame.K_UP] and player_y > box_rect.top:
                player_y -= player_speed
            if keys[pygame.K_DOWN] and player_y < box_rect.bottom - player_size:
                player_y += player_speed

        now = pygame.time.get_ticks()

        if game_over:
            pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, HEIGHT))
            go = get_bold_pixel_font(48).render("GAME OVER", True, RED)
            screen.blit(go, go.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
            sc = get_pixel_font(24).render(f"Score: {score}", True, WHITE)
            screen.blit(sc, sc.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            pr = get_pixel_font(24).render("Press SPACE to restart", True, WHITE)
            screen.blit(pr, pr.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))
        else:
            if current_state == WAITING and not game_over:
                if now - last_swarm_time >= arrow_cooldown:
                    current_state = FLASHING
                    flash_arrow = random.choice(["top", "left", "right"])
                    pending_swarm = spawn_arrows(flash_arrow, arrow_count)
                    flash_time = now

            elif current_state == FLASHING:
                if now - flash_time < 700:
                    draw_yellow_arrows(pending_swarm)
                else:
                    current_state = SPAWNING

            elif current_state == SPAWNING:
                arrows_list.extend(pending_swarm)
                pending_swarm.clear()
                last_swarm_time = now
                current_state = MOVING

            elif current_state == MOVING:
                for rect, d in arrows_list[:]:
                    if d == "top":
                        rect.y += 8
                    elif d == "left":
                        rect.x += 8
                    else:
                        rect.x -= 8

                    # remove arrow if outside box
                    if not box_rect.colliderect(rect):
                        arrows_list.remove((rect, d))
                        continue

                    # collision with player
                    if rect.colliderect(pygame.Rect(player_x, player_y, player_size, player_size)):
                        player_hp -= 1
                        arrows_list.remove((rect, d))
                        if player_hp <= 0:
                            game_over = True

                for rect, _ in arrows_list:
                    pygame.draw.rect(screen, BLUE, rect)

                draw_heart(player_x, player_y)
                draw_health_bar()

                if not arrows_list:
                    # all arrows gone, increase score
                    score += 1
                    arrow_cooldown = max(300, 1500 - score * 60)
                    arrow_count = 6 if score >= 40 else 5 if score >= 20 else 3 + score // 20

                    # enter breather pause before intermission
                    current_state = PAUSING
                    pause_start_time = now

            elif current_state == PAUSING:
                breather = get_breather_duration(score)
                draw_heart(player_x, player_y)
                draw_health_bar()
                if now - pause_start_time >= breather:
                    if radar_on:
                        current_state = INTERMISSION
                        selected_idx = 0
                    else:
                        # radar off → skip intermission
                        current_state = WAITING
                        last_swarm_time = pygame.time.get_ticks()
                        pending_swarm.clear()

            elif current_state == INTERMISSION:
                # show intermission buttons & selection heart
                draw_heart(player_x, player_y)
                draw_health_bar()

            draw_heart(player_x, player_y)
            draw_health_bar()
            
            # always draw buttons (shows heart on selected in INTERMISSION)
            draw_buttons()

            pygame.display.flip()
            clock.tick(60)

# main
while True: game_loop()
