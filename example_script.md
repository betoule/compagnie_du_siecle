component projector Projector 127.0.0.1:5000
component led Led 127.0.0.1:8080

# scene intro
    projector select 0
	led all 8fbaad
# scene 1
    projector select 1
	led all 5e5a9e
	projector play_sound unsettling_02-96366.mp3 0.5
# scene 2
	projector select 2
	led set 0-299 001133 0.1
	projector set_speed 50
	projector pan right
    projector play_sound unsettling_02-96366.mp3 0.5
	wait
	projector stop
# scene 3
    projector select 3
    projector viewport 512
	projector pan left
	wait
	projector stop
# scene 4
    projector select 4
    projector viewport 512
	projector pan left
	wait
	projector stop
