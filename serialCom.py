from PySide6.QtCore import QThread, Signal, Slot, QTimer
import serial
import serial.tools.list_ports
import time
from donnees import *

class SerialThread(QThread):
    # message_received = Signal(bytes)
    def __init__(self, port = None, baudrate = None):
        super().__init__()
        if port is not None:
            self.port = port
            self.baudrate = baudrate
            self.serial = serial.Serial(port, baudrate)
            self.running = True
        else:
            self.port = None
            self.baudrate = None
            self.serial = None
            self.running = False

        self.stateRx = 0
        self.compteurData = 0

        self.lastTime = time.time()

        self.msgError = ""


        self.FIFO_lecture = 0 #Pour le  buffer
        self.FIFO_occupation = 0
        self.FIFO_max_occupation = 0

    def run(self):#Thread qui gére la connexion
        while self.running:
            if self.serial.in_waiting > 0:
                byte = self.serial.read(1)
                # print(byte)
                # self.message_received.emit(byte)
                self.RxReceive(byte)
                # self.serial.write(b'\xFF')
                # sample_message = Message(id=1, length=3, data=[0x01, 0x02, 0x03])
                # packet = sample_message.build_packet()
                # self.serial.write(packet)
            if((time.time()-self.lastTime) > 3):#Pour annuler l'envoi du message toutes les 3 secondes si jamais il y a un probléme
                self.lastTime = time.time()
                if(com.ecritureEnCours):
                    com.ecritureEnCours = False
                    self.serial.cancel_write() 
                    com.problemeEnEcriture = True
            

    def close(self):
        if self.running:
            self.running = False
            self.serial.close()

    # @Slot(bytes)
    def RxReceive(self, message):#Fonction callback appellé a chaque arrivé d'un octet
        byte = int.from_bytes(message)
        # print(f"Received: {byte}")
        # print(f"Received: {message}")
        match self.stateRx:
            case 0:
                if byte == 0xff:
                    self.msgError = ""
                    self.msgError += " Header"
                    # print("Header")
                    self.stateRx = 1
                    com.rxMsg[com.FIFO_Ecriture].checksum = 0
            case 1:
                # print("ID")
                self.msgError += " ID" + str(byte.to_bytes())
                com.rxMsg[com.FIFO_Ecriture].id = int(byte)
                com.rxMsg[com.FIFO_Ecriture].checksum ^= byte
                self.stateRx = 2
            case 2:
                # print("len")
                self.msgError += " len" + str(byte.to_bytes())
                com.rxMsg[com.FIFO_Ecriture].len = int(byte)
                com.rxMsg[com.FIFO_Ecriture].checksum ^= byte
                com.rxMsg[com.FIFO_Ecriture].data = []
                self.compteurData = 0
                self.stateRx = 3
            case 3:
                # print("data n°", self.compteurData)
                self.msgError += " dt[" + str(self.compteurData) + "]= " + str(byte.to_bytes()) +"."
                com.rxMsg[com.FIFO_Ecriture].data.append(int(byte)) 
                com.rxMsg[com.FIFO_Ecriture].checksum ^= byte
                self.compteurData += 1
                if(self.compteurData >= com.rxMsg[com.FIFO_Ecriture].len):
                    self.compteurData = 0
                    self.stateRx = 4
            case 4:
                # print("checksum %d", byte)
                self.msgError += " checksum" + str(byte.to_bytes())
                if(com.rxMsg[com.FIFO_Ecriture].checksum == int(byte)):
                    self.stateRx = 5
                else :
                    self.stateRx = 0
                    print(self.msgError)
                    print(" ERROR Checksum mismatch msg n°"+ str(com.FIFO_Ecriture) +", "+ str(com.rxMsg[com.FIFO_Ecriture].checksum) + " != " + str(byte))
            case 5:
                # print("Header Fin")
                if byte == 0xFF:
                    self.msgError += " Header Fin"
                    print("Received new msg n°"+ str(com.FIFO_Ecriture) +" from id : ", com.rxMsg[com.FIFO_Ecriture].id.to_bytes())
                    com.FIFO_Ecriture = (com.FIFO_Ecriture + 1)%SIZE_FIFO
                print(self.msgError)
                self.stateRx = 0


    def RxManage(self):#Fonction à mettre à la suite de ton programme et à  compléter pour faire tes actions. Tu peux la mettre dans une autre classe stv
        # print("RxManage")
        self.FIFO_occupation = com.FIFO_Ecriture - self.FIFO_lecture
        if(self.FIFO_occupation<0):
            self.FIFO_occupation = self.FIFO_occupation + SIZE_FIFO
        if(self.FIFO_max_occupation < self.FIFO_occupation):
            self.FIFO_max_occupation = self.FIFO_occupation
        if(self.FIFO_occupation == 0):
            return

        match com.rxMsg[self.FIFO_lecture].id:
            case 0xA0:
                pass
            case 0xB0:
                print("Ack reçu")
            case _:
                print(f"Received message from an unknown ID")
        self.FIFO_lecture = (self.FIFO_lecture + 1) % SIZE_FIFO
    
    def sendMsg(self, msg = Message()):
        # sample_message = Message(id=1, length=3, data=[0x01, 0x02, 0x03])
        packet = msg.build_packet()
        print(packet)
        if com.serial_thread.running:
            try:
                com.ecritureEnCours = True
                com.serial_thread.serial.write(packet) #Fonction bloquante, qui se debloque toutes les 3 secondes si l'envoi à echouer
                com.ecritureEnCours = False
                if(com.problemeEnEcriture):
                    com.problemeEnEcriture = False
                    print(f"")
                    print(f"-----------Problème rencontré lors de l'envoi de données")
                    print(f"-----------Deconnexion du PORT COM...")
                    com.serial_thread.close()
                    print(f"-----------Essayer de vous reconnectez svp")
            except (serial.SerialException) as e:
                error_message = f"Failed to send data: {e.__class__.__name__}: {e}"
                print(error_message)
                print(f"")
                print(f"-----------{error_message}")
                com.serial_thread.close()
                print(f"-----------Essayer de vous reconnectez svp")
        else:
            print(f"")
            print(f"-----------Aucun PORT COM de connecté! Veuillez-vous connectez.")

    def sendEmpty(self, id):
        sample_message = Message(id, length=0, data=[0])
        self.sendMsg(sample_message)

    def sendByte(self, id, byte):
        sample_message = Message(id, length=1, data=[byte & 0xFF])
        self.sendMsg(sample_message)
    
    def sendTwoUint16(self, id, var1, var2):
        data = [
            var1 & 0xFF, (var1 >> 8) & 0xFF,
            var2 & 0xFF, (var2 >> 8) & 0xFF
        ]
        sample_message = Message(id, length=4, data=data)
        self.sendMsg(sample_message)

    def sendThreeUint16(self, id, var1, var2, var3):
        data = [
            var1 & 0xFF, (var1 >> 8) & 0xFF,
            var2 & 0xFF, (var2 >> 8) & 0xFF,
            var3 & 0xFF, (var3 >> 8) & 0xFF
        ]
        sample_message = Message(id, length=6, data=data)
        self.sendMsg(sample_message)
    
    def sendData(self, id, len = 0, dt = [0]):
        sample_message = Message(id, length=len, data=dt)
        self.sendMsg(sample_message)

com.serial_thread = SerialThread()
#end SerialThread