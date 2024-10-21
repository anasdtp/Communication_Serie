
import struct

SERIAL_BAUDRATE = 921600

# Listes de tous les id :
ID_CMD_MOUVEMENT     = 0xA0 #Commande de mouvement 
ID_ACK_GENERALE = 0xB0 #Ack generale

idComEnText = {
    0 : "",
    0xA0 : "ID_CMD_MOUVEMENT",
    0xA1 : "",
    0xB0 : "ID_ACK_GENERALE",
}

class Message():
    def __init__(self, id=0, length=0, data=None):
        self.id = id
        self.len = length
        self.data = data if data else []
        self.checksum = 0 #Le checksum est un XOR de tous les octect du message (de id, len et data[])
    
    def setData(self, id, length = 0, data = None):
        self.id = id
        self.len = length
        self.data = data if data else []

    def build_packet(self):
        # Calculate checksum
        self.checksum = (self.id ^ self.len) & 0xFF
        for i in range(self.len):
            self.checksum ^= self.data[i]
        length = self.len if(self.len) else 1 #Comme ça meme si on envoit un commande sans data, il faut forcément qu'il y est data0
        # Construct the packet with HEADEAR, ID, length, data, checksum, and FOOTER
        #For example : (FF A0 02 01 02 A1 FF)
        packet_format = f'<B B B {length}s B B'
        packet_data = bytes(self.data)
        return struct.pack(packet_format, 0xFF, self.id, self.len, packet_data, self.checksum, 0xFF)

SIZE_FIFO = 32 #Une FIFO est un buffer, la taille du buffer de reception est de 32
class COMMUNICATION():
    def __init__(self):
        self.rxMsg = [Message() for _ in range(SIZE_FIFO)]
        self.FIFO_Ecriture = 0
        self.serial_thread = None
        self.ecritureEnCours = False #Flag pour faire savoir qu'on a lancé une ecriture
        self.problemeEnEcriture = False #Flag pour dire que le serial.write n'a pas fonctionné
com = COMMUNICATION()
