component projector Projector 192.168.0.16:5000
component led Led 192.168.0.100

# scene 1: Narrateur
	led all 8fbaad
	wait
	projector play_sound coup_de_feu.mp3 1
	wait
	projector play_sound coup_de_feu.mp3 1
# scene 2 : maison
    projector select 01-maison.jpg
	led all 262525
	wait
	led all fefcff
# scene 3: maison
    projector select 01-maison.jpg
	led all fefcff
# scene 4 : Chocolaterie
    led all f7f7f7
	projector select 02-Mur.png
	#projector set_speed 50
	#projector viewport 
	#projector pan right
    wait
    projector play_sound Ticket.mp3 0.8
	wait
	projector select 03-Mur_chocovf2.png 1400
    wait
	projector stop
	wait
	projector set_speed 50
	projector pan left
	wait
	projector stop
    wait
	projector select 04-Porte.jpg
# scene 5 : Rivière
    led all f7a80a
	projector select 05-Rivière.jpg 2000
    projector set_speed 10
	projector pan right
	wait
	projector stop
	led all fcfcfc
	wait
	led all fa0505
	wait
	led all fcfcfc
	wait
# Interlude: Augustus
	projector play_sound Augustus.mp3 0.8
# scene 6 :Portes
    projector select 06-Préportes.jpeg
    led all 262525
    wait
	projector play_sound riviere.mp3 0.5
	wait
    led all fcfcfc
    projector set_speed 50
    projector select 07-Portes.png -600
	projector pan right	
    wait
    projector stop
# scene 7 : Machines
    projector select 10-Machines.jpg
    led all fcfcfc
	wait
	projector play_sound charging-machine-90403.mp3 0.8
    wait
    led all 2A3AEB
    wait
    led all 965FE9
    wait
    led all 6a1be0
    wait
# Interlude: Violette
    projector play_sound Violette.mp3 0.5
# scene 8 : Ecureuils
    led all fcfcfc
    projector select 11-noix.jpg
    wait
# Interlude: Veruca
    projector play_sound Veruca.mp3 0.5
# scene 9 : Ascenseur
    led all fcfcfc
    projector select 12-Ascenseur.jpg
    wait
    projector play_sound ascenseur.mp3 0.5
    wait
    projector play_sound ascenseur.mp3 0.5
    projector pan left
    wait
    projector play_sound ascenseur.mp3 0.5
    wait
    projector play_sound ascenseur.mp3 0.5
    projector pan left
    wait
    projector stop
# scene 10 : Télé
    led all fcfcfc
    projector select 13-télé.jpeg
    wait
    projector play_sound disparition.mp3 0.5
    led all AD0009
    wait 
    led all fcfcfc
    wait
    projector select 14-tablette.jpeg
    projector play_sound unsettling_02-96366.mp3 0.5
    led all 19AA1E
    wait
    led all fcfcfc
    projector select 13-télé.jpeg
    wait
    projector play_sound disparition.mp3 0.5
    led all AD0009
    wait
    led all fcfcfc
    wait
    projector select 15-mike.jpeg
    projector play_sound unsettling_02-96366.mp3 0.5
    led all 19AA1E
    wait
    led all fcfcfc
    projector select 13-télé.jpeg
    wait
# Interlude: Mike
    projector play_sound Mike.mp3 0.5
# scene 11 : Final
	projector select 13-télé.jpeg
	led all fcfcfc
# Salutations
    projector select 04-Porte.jpg
	led all fcfcfc
# Fin
	led all 111111
