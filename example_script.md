component projector Projector 127.0.0.1:5000
component led Led 127.0.0.1:8080

# scene intro
    projector select 0
	led all 8fbaad
	wait
	projector play_sound coup_de_feu.mp3 1
	wait
	projector play_sound coup_de_feu.mp3 1
# scene 1
    projector select 1
	led all 262525
	wait
	led set 0-299 f7f7f7 9
# scene 2
    led all f7f7f7
	projector select 2
	projector set_speed 50
	projector pan left
    wait
	projector select 3
    wait
	projector select 4
# scene 3
    led all f7a80a
    projector select 5
    projector viewport 500
    projector set_speed 10
	projector pan right
	wait
	projector stop
	led all fcfcfc
	wait
	led all fa0505
	wait
	led all fcfcfc
# scene 4
    led all 262525
    wait
    led all fcfcfc
    projector select 6
    projector viewport 0
	projector pan left	
    wait
    projector select 7
    projector viewport 100
	projector pan left
    wait
    projector select 8
    projector viewport 100
	projector pan left
# scene 5
    projector select 9
    led all fcfcfc
    wait
    led all 6a1be0
# scene 6
    led all fcfcfc
    projector select 10
    projector play_sound ecureuils.mp3 1
    wait
    projector stop
# scene 7
    led all fcfcfc
    projector select 11
    wait
    projector play_sound disparition.mp3 0.5
    wait
    projector play_sound unsettling_02-96366.mp3 0.5
    wait
    projector play_sound disparition.mp3 0.5
    wait
    projector play_sound unsettling_02-96366.mp3 0.5
    
