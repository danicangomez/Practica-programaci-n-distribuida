from paho.mqtt.client import Client
from multiprocessing import Process
import paho.mqtt.publish as publish

conexion = "picluster02.mat.ucm.es"

def procesa(mensaje):
    """
    Recibe un mensaje que descompone en jugador y celda y establece la nueva
    información de la celda para enviarla.
    En el caso de que un jugador ya haya hundido todos los barcos finaliza
    la partida.
    """
    player,fil,col = mensaje.split(',') 
    fil1 = int(fil)
    col1 = int(col)
    if player == 'player1': #Si el jugador es player1 lo que nos interesa es mirar
        board = 'board2'    #el tablero del otro jugador, y viceversa        
    else:
        board = 'board1'  
    data = datos[board][fil1][col1]
    
    """
    Asignamos un número según la información de cada celda para poder actualizar el
    mensaje en función de esta.
    0 := celda repetida con agua
    1 := celda repetida con barco
    2 := celda con agua
    3 := celda con barco
    """
    if data == 0 or data == 1:  #Si la celda ya ha sido elegida
        mensaje = player + ', ' + 'repetido'
        hundido = False
    else:
        if data == 3:    #Si la celda elegida es agua
            estado = 'agua'
            datos[board][fil1][col1] = 0   #Cambiamos su informacion a celda con agua ya marcada
            hundido = False     #Si la celda elegida contiene agua no hemos podido hundir ningún barco
        else:   #Si en la casilla que hemos elegido hay un barco
            datos[board][fil1][col1] = 1   #Cambiamos su informacion a celda con barco ya tocado
            if player == 'player1':
                hundido, estado = sunken_2(player, fil, col) #Si el barco lo ha elegido player1 comprobamos 
            else:                                            #si ha hundido un barco de player2, y viceversa.
                hundido, estado = sunken_1(player, fil, col)
        mensaje = player + ',' + estado + ',' + fil + ',' + col  #Enviamos mensaje con la información
    publi = Process(target=publicando,args=(mensaje,))
    publi.start()
    if hundido: #Si se ha hundido tenemos que comprobar si la partida ha acabado
         ha_acabado(player, estado, fil, col) 
    else:
         mensaje = player + ',' + ' Dame una celda: ' #Si no ha acabado, enviamos mensaje con la información
         pub = Process(target=publicando,args=(mensaje,))
         pub.start()
        
def ha_acabado(p,s,f,c):
    """
    Para cada jugador, comprueba si el diccionario donde se guardan
    los barcos del jugador rival está vacío y en ese caso finaliza la partida.
    De lo contrario, muestra que el barco se ha hundido pero siguen quedando
    barcos por hundir.
    """
    if p == 'player1':
        if barcos2 == {}:       #Si no quedan más barcos del otro jugador, la partida ha acabado
            mensaje = 'El ganador es: player1'
            publicar = Process(target=publicando,args=(mensaje,))
            publicar.start()
        else:                   #En caso contrario, enviamos mensaje con la información
            mensaje = p + ',' + s + ',' + f + ',' + c + ',' +' Dame una celda: '
            publicar = Process(target=publicando,args=(mensaje,))
            publicar.start()
    else:
        if barcos1 == {}:
            mensaje = 'El ganador es: player2'
            publicar = Process(target=publicando,args=(mensaje,))
            publicar.start()
        else:
            mensaje = p + ',' + s + ',' + f + ',' + c + ',' ' Dame una celda: '
            publicar = Process(target=publicando,args=(mensaje,))
            publicar.start()
            
def sunken_2(player,fil,col):
    """
    Comprueba en los barcos del player2 a partir de la celda dada si el barco
    ha sido hundido. En ese caso, actualiza su estado a hundido y elimina el
    barco del diccionario de los barcos del player2.
    Si el barco no ha sido hundido actualiza su estado a tocado.
    """
    fil1 = int(fil)
    col1 = int(col)
    celda = (fil1, col1)
    for key in barcos2.keys():          #Para cada clave en el diccionario de los barcos comprobamos
        if celda in barcos2[key]:       #si la celda esta en esa clave y la eliminamos
            barcos2[key].remove(celda)  
            solucion = key
            if len(barcos2[key])<1:  #Si no quedan celdas en esa clave, el barco se ha hundido
                hundido = True
                estado = 'hundido'
            else:
                hundido = False
                estado = 'tocado'
    if hundido:
        del barcos2[solucion]       #Si el barco se ha hundido lo quitamos del diccionario
    return(hundido,estado)

def sunken_1(player,fil,col):
    """
    Comprueba en los barcos del player1 a partir de la celda dada si el barco
    ha sido hundido. En ese caso, actualiza su estado a hundido y elimina el
    barco del diccionario de los barcos del player1.
    Si el barco no ha sido hundido actualiza su estado a tocado.
    """
    fil1 = int(fil)
    col1 = int(col)
    celda = (fil1,col1) 
    for key in barcos1.keys():
        if celda in barcos1[key]:
            barcos1[key].remove(celda)     #Realizacion la función análoga para el player2
            solucion = key                          
            if len(barcos1[key])<1:
                hundido = True
                estado = 'hundido'
            else:
                hundido = False
                estado = 'tocado'
    if hundido:
        del barcos1[solucion]
    return(hundido,estado)

def publicando(mensaje):
    #Función para publicar mensajes
    print(mensaje)
    publish.single('clients/game',payload=mensaje,hostname=conexion)

def on_message(mqttc,userdata,msg):
   mensaje = str(msg.payload)[2:-1]
   if datos['celdas'] == 0:  #Los jugadores envían sus barcos
       j,b,fil,col = mensaje.split(',')
       fil1=int(fil)
       col1=int(col)
       if j == 'player1':
           barcos1[b].append((fil1,col1)) #Añadimos los barcos del player1 al diccionario de sus barcos
           datos['board1'][fil1][col1] =2 #Cambiamos el 0 del agua por el 1 del barco
           if len(barcos1['b5']) == 2:    #cuando el ultimo barco está completo  
               datos['players'] += 1      #el jugador ya está listo para jugar
       else:
           barcos2[b].append((fil1,col1)) #Análogo para el otro jugador
           datos['board2'][fil1][col1] =2
           if len(barcos2['b5']) == 2:
               datos['players'] += 1
       if datos['players'] == 2:        #Cuando los dos jugadores estan listos envía un mensaje para empezar la partida
           men = 'Empezamos, dame una celda: '
           publicar = Process(target=publicando,args=(men,))
           publicar.start()
           datos['celdas'] = 1 
   else:
       procesa(mensaje)  #Comienza la partida y pasamos a procesar los mensajes de los jugadores

def crea_tablero(n):
    """
    Crea una lista de listas de tamaño n con un 0 en cada posición que usaremos para guardar la
    información de los barcos de cada jugador.
    """
    l = []
    for x in range(n):
        s= []
        for x in range(n):
            s.append(3)
        l.append(s)
    return l

tab1 = crea_tablero(10)
tab2 = crea_tablero(10)
datos = {'board1':tab1, 'board2':tab2, 'players': 0, 'celdas':0}
barcos2 = {'b1':[],'b2':[],'b3':[],'b4':[],'b5':[]}
barcos1 = {'b1':[],'b2':[],'b3':[],'b4':[],'b5':[]}


mqttc = Client(userdata=(datos,barcos1,barcos2))
mqttc.on_message = on_message
mqttc.enable_logger()

mqttc.connect(conexion)
mqttc.subscribe('clients/players') #Para recibir mensajes
mqttc.loop_forever()
