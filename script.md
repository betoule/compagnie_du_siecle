#component projector Projector 192.168.0.16:5000
#component led Led 192.168.0.100
component projector Projector 127.0.0.1:5000
component led Led 127.0.0.1:8080

# scene 1: Narrateur
    projector play_sound theatre_ouverture.mp3 1
	led all 8fbaad
    projector select 01-maison.jpg
	#Je veux regarder la télé
	wait
	projector play_sound coup_de_feu.mp3 1
	wait
	projector play_sound coup_de_feu.mp3 1
# scene 2 : maison
    projector select 01-maison.jpg
	led all 131202
	#voyons voir ce qui se passe chez les Bucket... À plus tard
	wait
	led all fefcff
# scene 3: maison
    projector select 01-maison.jpg
	led all fefcff
# scene 4 : Chocolaterie
    led all 151520
	projector select 02-Mur.png
	#projector set_speed 50
	#projector viewport 
	#projector pan right
	#Voyons voir... Il est écrit dessus
    wait
    projector play_sound Ticket.mp3 0.8
    #Et aujourd'hui nous sommes le 1er février
	wait
	projector select 03-Mur_chocovf3.png 1400
    wait
	projector stop
	wait
	projector set_speed 50
	projector pan left
	wait
	projector stop
	#Voilà, nous y sommes
    wait
	projector select 04-Porte.jpg
# scene 5 : Rivière
    led all 472210
	projector select 05-Rivière.jpg 2000
    projector set_speed 10
	projector pan right
	wait
	projector stop
	led all 573220
	#Fais attention Augustus, tu te penches trop en avant
	wait
	led all fa0505
	#Ça y est, le voilà parti
	wait
	led all 573220
	wait
# scene Interlude: Augustus
	projector play_sound Augustus.mp3 0.8
# scene 6 :Portes
    projector select 06-Préportes.jpeg
    led all 200505
    #Comment ces stupides oompa-lommpas font ils pour voir où ils vont
    wait
	projector play_sound riviere.mp3 0.5
	#Allumez les lumières
	wait
    led all fcfcfc
    projector set_speed 50
    projector select 07-Portes.png -600
	projector pan right	
	# Arrêtez le bateau
    wait
    projector stop
# scene 7 : Machines
    projector select 10-Machines.jpg
    led all 301000
    #C'est parti
	wait
	projector play_sound charging-machine-90403.mp3 0.8
	# Tout ton visage devient bleu
    wait
    led all 2A3AEB
    #Ma fille devient toute bleue et toute mauve
    wait
    led all 965FE9
    # Violette tu deviens violette
    wait
    led all 6a1be0
    #Sauvez-la
    wait
	led all 301000
# scene Interlude: Violette
    projector play_sound Violette.mp3 0.5
# scene 8 : Ecureuils
    led all fcfcfc
    projector select 11-noix.jpg
    wait
# scene Interlude: Veruca
    projector play_sound Veruca.mp3 0.5
# scene 9 : Ascenseur
    led all fcfcfc
	projector set_speed 250
    projector select 12-Ascenseur.jpg
    #Accrochez vous tout le monde
    wait
    projector play_sound ascenseur.mp3 0.5
	projector pan up
    wait
    projector play_sound ascenseur.mp3 0.5
    projector pan left
    wait 
    projector play_sound ascenseur.mp3 0.5
	projector pan down
    wait
    projector play_sound ascenseur.mp3 0.5
    projector pan right
    wait
	projector stop
    projector play_sound ascensur_fin.mp3 0.5
    wait
# scene 10 : Télé
    led all fcfcfc
    projector select 13-télé.jpg
    # maintenant allumez !
    wait
    projector play_sound disparition.mp3 0.5
    led all AD0009
	# Le chocolat a disparu
    wait 
    led all fcfcfc
	# Regardez l'écran
    wait
    projector select 14-tablette.jpg
    projector play_sound unsettling_02-96366.mp3 0.5
    led all 19AA1E
	# Prenez la
    wait
    led all fcfcfc
	# C'est fantastique
	wait
    projector select 13-télé.jpg
	# À plus tard/ à tout de suite
    wait
    projector play_sound disparition.mp3 0.5
    led all AD0009
	# Il n'est plus là
    wait
    led all fcfcfc
	# Le voici
    wait
    projector play_sound unsettling_02-96366.mp3 0.5
    led all 19AA1E
	projector select 15-mike.jpg
	# Attrapez le vite
    wait
    led all fcfcfc
    projector select 13-télé.jpeg
    wait
# scene Interlude: Mike
    projector play_sound Mike.mp3 0.5
# scene 11 : Final
	projector select 13-télé.jpg
	led all fcfcfc
# scene Salutations
    projector select 04-Porte.jpg
	led all fcfcfc
# scene Fin
	led all 111111
