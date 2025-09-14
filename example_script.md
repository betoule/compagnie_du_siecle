#component projector Projector 192.168.0.45:5000
component led Led 127.0.0.1:8080

# scene intro
	led all 8fbaad
	wait
	projector play_sound coup_de_feu.mp3 1
	wait
	projector play_sound coup_de_feu.mp3 1
# scene 1 : maison
    projector select 01-maison.jpg
	led all 262525
	wait
	led all fefcff
# scene 2 : Chocolaterie
    led all f7f7f7
	projector select 02-Mur.png
	projector set_speed 50
	#projector viewport 
	projector pan right
    wait
    projector play_sound Ticket.mp3 1
    wait
	projector select 03-Mur_chocovf2.png
	projector viewport 2018
	projector pan left
	wait
	projector stop
    wait
	projector select 04-Porte.jpg
# scene 3 : Rivière
    led all f7a80a
    projector select 05-Rivière.jpg
    projector viewport 910 
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
	projector play_sound Augustus.mp3 1
# scene 4 :Portes
    projector select 06-Préportes.jpeg
    led all 262525
    wait
    projector play_sound riviere.mp3
    wait
    led all fcfcfc
    projector set_speed 20
    projector select 07-Portes.png
    projector viewport 0
	projector pan right	
    wait
    projector stop
# scene 5 : Machines
    projector select 10-Machines.jpg
    led all fcfcfc
    wait
    led all 2A3AEB
    wait
    led all 965FE9
    wait
    led all 6a1be0
    wait
    projector play_sound Violette.mp3 1
# scene 6 : Ecureuils
    led all fcfcfc
    projector select 11-noix.jpg
    wait
    projector play_sound Veruca.mp3 1
# scene 7 : Ascenseur
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
# scene 8 : Télé
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
    projector play_sound Mike.mp3 1
    
