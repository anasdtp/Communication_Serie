from serialCom import *

ID_CMD_GENERAL = 0xA0 
ID_CMD_XYT = 0xA1 

ID_ACK_GENERAL = 0xC0 

ID_REPEAT_REQUEST = 0xD0
ID_POS_XYT = 0xD1

idComEnText = {
    0 : "",
    0xA0 : "ID_CMD_GENERAL",
    0xA1 : "ID_CMD_XYT",
    0xC0 : "ID_ACK_GENERAL",
    0xD0 : "ID_REPEAT_REQUEST",
    0xD1 : "ID_POS_XYT"
}

def start_serial(selected_port = "COM4"):
        # selected_port = self.dialog.ui.comboBox.currentText()
        print(selected_port)
        if selected_port:
            try:
                com.serial_thread = SerialThread(selected_port, SERIAL_BAUDRATE)
                com.serial_thread.start()
                print("Starting serial com")
            except serial.SerialException as e:
                print("Serial Error", f"Failed to open port {selected_port}: {e}")

def Afficher_Port_Disponible():
        print("Afficher Port Disponible")
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(port.device)

class MaClassePrincipale():
    def __init__(self):
        self.FIFO_lecture = 0
        self.FIFO_max_occupation = 0
        self.FIFO_occupation = 0
    
    def rxManage(self):#Fonction à mettre à la suite de ton programme et à  compléter pour faire tes actions. Tu peux la mettre dans une autre classe stv
        # print("RxManage")
        self.FIFO_occupation = com.FIFO_Ecriture - self.FIFO_lecture
        if(self.FIFO_occupation<0):
            self.FIFO_occupation = self.FIFO_occupation + SIZE_FIFO
        if(self.FIFO_max_occupation < self.FIFO_occupation):
            self.FIFO_max_occupation = self.FIFO_occupation
        if(self.FIFO_occupation == 0):
            return
        
        id = com.rxMsg[self.FIFO_lecture].id
        print("\n")
        print("Received message from id: ", idComEnText.get(id, "ID inconnu"))
        
        match id:
            case id if id == ID_CMD_GENERAL:
                pass
            case id if id == ID_ACK_GENERAL:
                print("Ack reçu")
            case id if id == ID_REPEAT_REQUEST:
                print("Repeat request")
            case id if id == ID_POS_XYT:
                print("XYT command")
                x = com.rxMsg[self.FIFO_lecture].data[0] + (com.rxMsg[self.FIFO_lecture].data[1] << 8)
                y = com.rxMsg[self.FIFO_lecture].data[2] + (com.rxMsg[self.FIFO_lecture].data[3] << 8)
                theta = com.rxMsg[self.FIFO_lecture].data[4] + (com.rxMsg[self.FIFO_lecture].data[5] << 8)
                print(f"x: {x}, y: {y}, theta: {theta}")
            case _:
                print(f"Received message from an unknown ID")
        self.FIFO_lecture = (self.FIFO_lecture + 1) % SIZE_FIFO
            

def main():
    print("Main")
    principale = MaClassePrincipale()

    Afficher_Port_Disponible()
    start_serial("COM5")
    print("Sending msg")
    com.serial_thread.sendByte(ID_CMD_GENERAL, 1)

    x = 500 #en mm
    y = 1000 #en mm
    theta = 900 #en dizieme de degré
    com.serial_thread.sendThreeUint16(ID_CMD_XYT, x, y, theta)

    while(1):
         principale.rxManage() # On lit le buffer et on traite les message


if __name__ == "__main__":
    main()