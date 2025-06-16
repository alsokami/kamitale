"""
small notes:

- all times are in ms (1s = 100ms)
- all sizes are in pixels

"""

# importing libraries
import pygame
from pygame import mixer # mixer is used to play audoi from pygame
import random
import sys

pygame.init() # initialize pygame
pygame.mixer.init() # initialize the music player

# display config
WIDTH, HEIGHT = 650, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("kamitale")

# font caching - needed. this is used to only take the text needded in frame
font_cache = {} # create a list of the characters needed for the cache
def bold_font(size):
    key = f"bold_{size}"
    if key not in font_cache:
        font_cache[key] = pygame.font.Font("bold_font_8.ttf", size) # bold font
    return font_cache[key] # returns the needed characters from the font

def font(size): return pygame.font.Font("PixelOperator.ttf", size) # get main font

# SFX import
battleost = mixer.Sound("spider_dance.mp3")
strikedsfx = mixer.Sound("strike.mp3")
healsfx = mixer.Sound("heal.mp3")
noheals = mixer.Sound("noneleft.mp3")
shattersfx = mixer.Sound("soul_shatter.mp3")
gameoverost = mixer.Sound("game_over.mp3")

mixer.Channel(1).play(battleost, loops=-1) # play the music ost on the first channel

# color setup - obtainable from the hex color picker on google
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

# box config
BOX_SIZE = 250 # size of the box
box = pygame.Rect((WIDTH - BOX_SIZE) // 2, (HEIGHT - BOX_SIZE) // 2 + 50, BOX_SIZE, BOX_SIZE)

# player config
playersize = 20 # this will scale the image of the heart
player_x, player_y = box.center
hp = maxhealth = 2
level = 1

# swarm config
arrow_count = 3 # starting number, will change the start. this is dynamic anyway
arrow_cooldown = 1500
last_swarm_time = flash_time = 0

# game states (this is when the game switches from waiting for arrows, spawning arrows, etc)
""" game states:
waiting - the user freely moves inside of the box, waiting for a swarm of arrows
flashing - yellow pointer arrows point to where the arrows in the swarm will go to
spawning - the game spawns the swarms of arrows
moving - the arrows move inside of the box to their destination
pausing - the arrows are gone, and the player is given a brief breather
intermission - the player can interact with the four boxes
"""
WAITING, FLASHING, SPAWNING, MOVING, PAUSING, INTERMISSION = range(6)
current_state = WAITING # start in the box

arrow_width, arrow_height = 15, 60 # this will change the size of the image
arrowimg = pygame.transform.scale(pygame.image.load("arrow.png").convert_alpha(), (arrow_width, arrow_height))
pointerimg = pygame.transform.scale(pygame.image.load("pointer.png").convert_alpha(), (30, 30))
heartimg = pygame.transform.scale(pygame.image.load("heart.png").convert_alpha(), (playersize, playersize))
clock = pygame.time.Clock()

def health_bar(): # the health bar, HP text, center it with box
    bar_w, bar_h = 100, 15
    y = box.bottom + 10
    lvl_s = bold_font(24).render(f"LVL {level}", True, WHITE)
    hp_s = bold_font(24).render("HP", True, WHITE)
    space1, space2 = 20, 10
    total_w = lvl_s.get_width() + space1 + hp_s.get_width() + space2 + bar_w
    x = (WIDTH - total_w) // 2
    screen.blit(lvl_s, (x, y))
    screen.blit(hp_s, (x + lvl_s.get_width() + space1, y))
    bar_x = x + lvl_s.get_width() + space1 + hp_s.get_width() + space2 # health bar config
    pygame.draw.rect(screen, RED, (bar_x, y, bar_w, bar_h))
    pygame.draw.rect(screen, YELLOW, (bar_x, y, bar_w * (hp / maxhealth), bar_h)) # taxes the size of the other rect, and times width by hp divided by maxhealth to cover the percentage left

def buttons(): # draw the buttons and text inside, center them
    start_x = (WIDTH - 4*100 - 3*10) // 2 # i played around with the positions, do not change
    for i, name in enumerate(["ATTACK","ACT","ITEM","MERCY"]): # easily put the text without too much nesting
        btn = pygame.Rect(start_x + i*110, HEIGHT - 80, 100, 50)
        pygame.draw.rect(screen, BLACK, btn)
        pygame.draw.rect(screen, (255,165,0), btn, 3)
        icon_x, icon_y = btn.x+8, btn.centery # put the button with 8 padding on X from the center
        if current_state == INTERMISSION and i == selected_idx: # if the user is on intermission, replace the symbol wit hthe heart
            screen.blit(heartimg, (icon_x-5, icon_y-10))
        else: # drawing the shapes of each box
            if name == "ATTACK":
                pygame.draw.line(screen, (255,165,0), (icon_x,icon_y), (icon_x+15,icon_y), 3)
            elif name == "ACT":
                pygame.draw.circle(screen, (255,165,0), (icon_x+10,icon_y), 10, 3)
            elif name == "ITEM":
                pygame.draw.polygon(screen, (255,165,0), [(icon_x,icon_y-10),(icon_x+20,icon_y-10),(icon_x+10,icon_y+10)])
            else:
                pygame.draw.line(screen, (255,165,0), (icon_x,icon_y-15), (icon_x+30,icon_y+15), 3)
                pygame.draw.line(screen, (255,165,0), (icon_x+30,icon_y-15), (icon_x,icon_y+15), 3)
        for size in range(24,5,-1): # get the font for dynamic text scaling 
            txt = bold_font(size).render(name, True, (255,165,0))
            padding = 5
            symbol_space = 20
            if (txt.get_width() + symbol_space + padding*2) <= btn.width and (txt.get_height() + padding*2) <= btn.height:
                screen.blit(txt, (btn.centerx - txt.get_width()//2, btn.centery - txt.get_height()//2))
                break

def pointer_arrows(swarm): # drawing the pointer arrows and rotating the images
    for rect, d in swarm:
        if d == "top": # if the arrow comes from the top, rotate the arrow 180 to face bottom
            img = pygame.transform.rotate(pointerimg, 180); pos=(rect.x+arrow_width//2-15, box.top-30)
        elif d == "bottom": # if the arrow comes from the bottom (only once), don't rotate
            img = pointerimg; pos=(rect.x+arrow_width//2-15, box.bottom+10)
        elif d == "left": # if arrow comes from left, rotate it 90 deg clockwise to opint to the right
            img = pygame.transform.rotate(pointerimg, -90); pos=(box.left-30, rect.y+arrow_width//2-15)
        else: img = pygame.transform.rotate(pointerimg, 90); pos=(box.right+10, rect.y+arrow_width//2-15) # same as left but for opposite sides
        screen.blit(img, pos)

def spawn_arrows(direction, count): # spawning the blue arrows
    swarm = [] # create an empty list of arrows (this is needed so the game can have multiple arrows at random positions)
    for i in range(count):
        if direction == "top": # if it goes from the top to bottom
            x = box.left + random.randint(0, BOX_SIZE-arrow_width) # take a random place around the box
            y = box.top + i*(arrow_height//2) # gradually move the arrow
        elif direction == "bottom": # all the rest is the same as before
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

def arrow_swarm(): # rotating the arrows and putting the image
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

background = pygame.Surface((WIDTH, HEIGHT)) # make the background black
background.fill((0, 0, 0))
pygame.draw.rect(background, (200, 200, 200), pygame.Rect((WIDTH - 250) // 2, (HEIGHT - 250) // 2 + 50, 250, 250), 3)

def game(): # game loop. this was made in a function to call other functions and have variables only set once rather than multiple times with the while True
    # take the variables from other functions
    global radar_on, selected_idx, player_x, player_y, arrows_list, score, hp, arrow_cooldown, first_swarm
    global current_state, pending_swarm, flash_arrow, last_swarm_time, flash_time, arrow_count
    
    # note: there is a paste called "current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()" that will change the state to waiting, the swarm to -, and the last swarm time to now, setting the game back as it should, waiting for a swarm.
    
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
    heals = 3
    current_state = 0
    pending_swarm = []
    flash_arrow = None
    game_over = False
    pause_start = 0
    
    
    # drawing the circle for the enemy guy on top of the box
    radius = 15
    cx = box.centerx
    cy = box.top - 30 # do not change
    color = (0, 0, 0) # doesn't really matter
    enemyimg = pygame.image.load("enemy_sprite.gif")
    enemy = pygame.transform.scale(enemyimg.convert_alpha(), (radius + 60, radius + 60)) # do not change
    
    while True:
        screen.blit(heartimg, (player_x, player_y)) # make the heart always the image
        health_bar() # call the function
        buttons() # same as above
        
        now = pygame.time.get_ticks() # get the present tick
        screen.blit(background, (0, 0)) # make the background permantnly white
        enemybox = pygame.draw.circle(screen, color, (cx, cy), radius) # draw the enemy on the circle
        screen.blit(enemy, (cx - 35, cy - 60)) # replace the circle, dont change padding
        
        screen.blit(heartimg, (player_x, player_y)) # change the heart to the heart image and make it move with it
        # re call functions in case the background is updated too much
        health_bar()
        buttons()

        for e in pygame.event.get(): # get all the events
            if e.type == pygame.QUIT: # close game on clicking X
                pygame.quit()
                sys.exit()

            if e.type == pygame.KEYDOWN: # if a key is down
                if e.key == pygame.K_x: # if X is enabled, turn on the intermission skipper
                    radar_on = not radar_on
                if not radar_on and current_state == INTERMISSION: # skip the intermission
                    current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()
                if game_over and e.key == pygame.K_SPACE: # if space is pressed on game over
                    mixer.Channel(3).stop() # stop the game over song
                    mixer.Channel(1).play(battleost, loops=-1) # put back the sbattle ost
                    return
                if current_state == INTERMISSION: # if its intermission
                    if e.key in (pygame.K_a, pygame.K_LEFT): # left arrow moves you one to the left
                        selected_idx = (selected_idx - 1) % 4
                    if e.key in (pygame.K_d, pygame.K_RIGHT): # right arrow moves you one to the right
                        selected_idx = (selected_idx + 1) % 4
                    if e.key in (pygame.K_z, pygame.K_RETURN): # if you click on enter, events happen
                        if selected_idx == 2: # if its the item box, do the following
                            if heals == 0: # if the player has no more heals left, dont do anything but play the noheals sfx
                                mixer.Channel(2).play(noheals)
                                current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()
                            elif hp < maxhealth: # if the player has less health than max
                                hp += 1 # heal for one 
                                heals -=1 # take away one heal
                                mixer.Channel(2).play(healsfx) # play the heal sfx
                                current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()
                            else: # if the player has max health, but has heals
                                mixer.Channel(2).play(strikedsfx) # play the fail noise (there's no need to). this won't take away a heal
                                current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()
                        else: # if it's any other button, skip
                            current_state, pending_swarm, last_swarm_time = WAITING, [], pygame.time.get_ticks()
        if not game_over and current_state != INTERMISSION: # any other states than intermission
            keys = pygame.key.get_pressed() # get the key pressed for movement
            speed = 5.7 + (6.2 - 5.7) * min(score, 30) / 30 # make the movement faster as the game goes on
            # LRUD keystrokes
            if keys[pygame.K_LEFT] and player_x > box.left: player_x -= speed
            if keys[pygame.K_RIGHT] and player_x < box.right - playersize: player_x += speed
            if keys[pygame.K_UP] and player_y > box.top: player_y -= speed
            if keys[pygame.K_DOWN] and player_y < box.bottom - playersize: player_y += speed
            if current_state == WAITING and now - last_swarm_time >= arrow_cooldown: # if waiting for swarm
                if first_swarm: # if it's the first swarm of the game, be the only one coming from the bottom
                    direction = "bottom"
                    first_swarm = False # its not the first swarm anymore
                else: # take a random chioce of direction if its not first (see how it's not bottom)
                    direction = random.choice(["top", "left", "right"]);
                current_state = FLASHING # after taking the choice, put the state to flashing
                flash_arrow = direction # put the arrow on the direction
                pending_swarm = spawn_arrows(direction, arrow_count) # pending swarm is the arrows to the direction of the yellow ones. the blue swarm isn't random, the yellow ones are
                flash_time = now # flash now
        if not game_over and current_state == FLASHING and now - flash_time < 700: # if it's been less than 0.7s
            pointer_arrows(pending_swarm) # point the yellow arrows
        if not game_over and current_state == FLASHING and now - flash_time >= 700: # if it hasnt, spawn arrows
            current_state = SPAWNING
        if not game_over and current_state == SPAWNING: # if theyre spawning
            arrows_list += pending_swarm # add the arrows to the list 
            pending_swarm = [] # no more pending since they're spawning
            last_swarm_time = now # last swarm time is right now
            current_state = MOVING # the arrows are moving
        if not game_over and current_state == MOVING: # if the arrows are moving
            for arrow in arrows_list[:]: # make the arrows move in a rectangle hitbox
                rect, d = arrow
                if d == "top": rect.y += 8
                elif d == "left": rect.x += 8
                elif d == "right": rect.x -= 8
                elif d == "bottom": rect.y -= 8

                if not box.colliderect(rect): # if they haven't collided with the box rectangle and it's not on the list, remove them
                    if arrow in arrows_list:
                        arrows_list.remove(arrow)
                    continue

                if rect.colliderect(pygame.Rect(player_x, player_y, playersize, playersize)): # if they touch the player hitbox
                    hp -= 1 # take away one health
                    mixer.Channel(2).play(strikedsfx) # play the striked sound effect on another channel to avoid overlapping music
                    if arrow in arrows_list:
                        arrows_list.remove(arrow)
                    if hp <= 0: # if player dies
                        mixer.Channel(1).stop() # stop all sfx
                        mixer.Channel(2).stop()
                        ch = pygame.mixer.Channel(3) # play the shatter, then game over
                        ch.play(shattersfx)
                        ch.queue(gameoverost)
                        game_over = True # game is over

                heart_rect = pygame.Rect(player_x + 4, player_y + 4, playersize - 8, playersize - 8) # hitbox is the player but bigger
                arrow_hitbox = rect.copy() # the arrow hitbox is around it. the arrow image itself replaces a rectangle, so we're copying that same rectangle but using it as a hitbox
                if d in ["left", "right"]: # there was a glitch where it would hit the player at all times if it came from the left or right, so i made it smaller when coming from right and left and it fixed it
                    arrow_hitbox.inflate_ip(-6, 0)

                if arrow_hitbox.colliderect(heart_rect): # if the arrow and player touch
                    hp -= 1 # take away health
                    mixer.Channel(2).play(strikedsfx) # play striked sfx
                    if arrow in arrows_list:
                        arrows_list.remove(arrow)
                    if hp <= 0: # same game over snippet
                        mixer.Channel(1).stop()
                        mixer.Channel(2).stop()
                        ch = pygame.mixer.Channel(3)
                        ch.play(shattersfx)
                        ch.queue(gameoverost)
                        game_over = True

            arrow_swarm() # spawn swarm
        if not game_over and current_state == MOVING and not arrows_list: # if arrows are moving
            score += 1; arrow_count = 6 if score >= 40 else 5 if score >= 20 else 3 + score // 20 # the score is +1 if they survive dodging
            arrow_cooldown = max(300, 1500 - score * 60) # cooldown gets smaller over score
            current_state, pause_start = PAUSING, now # now you get a small breather
        if not game_over and current_state == PAUSING and now - pause_start >= 700 * (1 - min(score, 30) / 30): # the player gets a tiny breather before the intermission
            current_state = INTERMISSION if radar_on else WAITING # if the radar is on, go waiting. if not, go intermission.
            if current_state == WAITING: last_swarm_time = now # last swarm was just rn

        if game_over: # if the game over, fill in black and put the game over text
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
