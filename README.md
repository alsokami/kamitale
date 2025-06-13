# KAMITALE - AN UNDERTALE FANGAME

kamitale is a school summative project coded in full pygame in order to replicate an undyne like fight with a twist.
this is a beginner made project. no updates will be scheduled. 

# FEATURES

![image](https://github.com/user-attachments/assets/e58cabcc-3ace-48e8-a57e-ba8853f8e729)


by version 1.1 - we have added a radar switch that can skip the intermission phase (where the user can use the buttons). 
the text size offset is still to be changed and fixed soon. we are planning on adding features to each of the buttons soon.

# CODE STRUCTURE

- the game uses font caching in order to load the fonts and assets without taking a toll on the performance of the game.
- the game has a main function called game_loop, to switch between different states of the game without looping forever and causing the code to break.

### GAME STATES

1. WAITING - the user freely moves inside of the box, waiting for a swarm of arrows
2. FLASHING - yellow pointer arrows point to where the arrows in the swarm will go to
3. SPAWNING - the game spawns the swarms of arrows
4. MOVING - the arrows move inside of the box to their destination
5. PAUSING - the arrows are gone, and the player is given a brief breather
6. INTERMISSION - the player can interact with the four boxes
