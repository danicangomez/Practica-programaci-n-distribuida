from paho.mqtt.client import Client
import pygame

fondo = (0, 0, 0)
color_inicial = (255, 255, 255)
mar = (0,0,255)
amarillo = (255, 255, 0)
barco_tocado = (255, 0, 0)
largo  = 20
alto = 20
tablero_1 = 10
tablero_2 = 22
separacion = 5 
tamaño_ventana = [560,260]
conexion = "picluster02.mat.ucm.es"

"""
CÓDIGO DE COLORES
-----------------
Agua: mar
Barcos al inicio: amarillo
Barcos tocados o hundidos: barco_tocado
"""

def color_set(estado):
    """
    Definimos el color del que pintamos una celda
    en función del estado de esta
    """
    if estado == 'agua':
        return mar
    else:
        return barco_tocado

def on_message(mqttc, userdata, msg):
    mensaje = str(msg.payload)[2:-1] #Quitamos la parte innecesaria del mensaje
    if mensaje == 'El ganador es: player1' or mensaje == 'El ganador es: player2':
        print(mensaje)     
        pygame.quit()                #Si uno de los diccionarios de barcos está vacío acabamos la partida   
    elif mensaje == 'player1, Dame una celda: ':
        pass                         #Es un mensaje para el otro jugador
    elif len(mensaje) == 17:         #Es una celda repetida
        p, repetido = mensaje.split(',')
        if p == 'player2':
            print('Ya habías elegido esta celda')
            t[1] = True              #Ejecutamos el bucle del final
    elif mensaje == 'Empezamos, dame una celda: ' or mensaje == 'player2, Dame una celda: ':
        t[1] = True                  #Ejecutamos el bucle del final
    elif len(mensaje) == 37:         #Se ha hundido un barco pero la partida no ha concluido
        player, estado, fil, col, frase = mensaje.split(',')
        color = color_set(estado)
        fil1 = int(fil)
        col1 = int(col)
        if player == 'player1':
            fil1 = fil1
            col1 = col1
        else:
            fil1 = fil1
            col1 = col1 + 12      #Para poder pintar en el tablero rival
            print('Enhorabuena! Barco hundido!' + frase)
        t[1] = True               #Ejecutamos el bucle del final
        pygame.init()
        tablerop1[fil1][col1] = color   #Cambiamos el color de la celda
        pantalla = pygame.display.set_mode(tamaño_ventana)
        pantalla.fill(fondo)
        pygame.display.set_caption("Hundir la flota")
        #Actualizamos el tablero
        for filas in range(tablero_1):
            for columnas in range(tablero_2):
                color_celda = tablerop1[filas][columnas]
                pygame.draw.rect(pantalla, color_celda, [(separacion + largo) * columnas + separacion,
                              (separacion + alto) * filas + separacion, largo, alto])
        pygame.display.flip()
    else:               #Contemplamos el resto de los casos (agua, barco tocado)
        player, estado, fil, col = mensaje.split(',')
        color = color_set(estado)
        fil1 = int(fil)
        col1 = int(col)
        if player == 'player1':
            fil1 = fil1
            col1 = col1
        else:
            if estado == 'agua':
                print('Agua!')
                t[1] = True          #Ejecutamos el bucle del final
            elif estado == 'tocado':
                print('Barco tocado!')
                t[1] = True          #Ejecutamos el bucle del final
            fil1 = fil1 
            col1 = col1 + 12
        pygame.init()
        tablerop1[fil1][col1] = color  #Cambiamos el color de la celda
        pantalla = pygame.display.set_mode(tamaño_ventana)
        pantalla.fill(fondo)
        pygame.display.set_caption("Hundir la flota")
        #Actualizamos el tablero
        for filas in range(tablero_1):
            for columnas in range(tablero_2):
                color_celda = tablerop1[filas][columnas]
                pygame.draw.rect(pantalla, color_celda, [(separacion+largo) * columnas + separacion,
                              (separacion+alto) * filas + separacion, largo, alto])
        pygame.display.flip()
            
def p_board(f, c):
    """
    Creamos el tablero como una matriz  (f x c) en la que pintamos 
    cada celda según su estado inicial
    """
    board = []
    for fil in range(f):
        board.append([])
        for col in range(c):
            if col == 10 or col == 11:
                board[fil].append(fondo)
            else:
                if (fil, col) in barcos:
                    board[fil].append(amarillo)
                else:
                    board[fil].append(color_inicial)
    return board

boats = input('Dame fichero con los barcos: ')

def get_boats(b):
    """
    Leemos el fichero que hemos añadido y creamos una lista con las celdas
    donde hay barcos, a partir de la cual crearemos el tablero.
    """
    archivo = open(b, 'r')
    l = []
    n = 1
    for linea in archivo:
        a, b = linea.split()
        fil = int(a)
        col = int(b)
        l.append((fil, col))
        n += 1
    return l

barcos = get_boats(boats)
tablerop1 = p_board(tablero_1, tablero_2)
t = [tablerop1,False]

mqttc = Client(userdata = t)
mqttc.on_message = on_message
mqttc.enable_logger()

mqttc.connect(conexion)
mqttc.subscribe('clients/game')  #Para recibir mensajes


mqttc.loop_start()


n = 1
for c in barcos:
    a, b = c
    if n < 6:
        barco = 'b1'
    elif n < 10:
        barco = 'b2'
    elif n < 13:
        barco = 'b3'
    elif n < 16:
        barco = 'b4'
    else:
        barco = 'b5'
    n += 1
    mensaje = 'player2,' + barco + ',' + str(a) + ',' + str(b)
    mqttc.publish('clients/players', mensaje)
    
#Cuando t[1] es True pedimos la siguiente celda
    
while True:
    
    if t[1]:
        celda = input('Dame una celda: ')
        mens = 'player2' + ',' + celda
        t[1] = False
        mqttc.publish('clients/players', mens) #Para publicar mensajes