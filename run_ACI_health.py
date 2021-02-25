from threading import Thread
import time
from modules.ACI_services import AciInventory, AciHealth
from modules.DNA_services import DNAGetInventory, DNAGetHealth
import os, sys

def inventory():
    print('Starting inventory service')
    while True:
        AciInv.run()
        DnaInv.run()
        time.sleep(2800)

def health():
    print('Starting health service')
    time.sleep(240)
    while True:
        AciHl.run()
        DnaHl.run()
        time.sleep(120)

if __name__ == '__main__':

    AciInv = AciInventory()
    DnaInv = DNAGetInventory()
    AciHl = AciHealth()
    DnaHl = DNAGetHealth()
    t1 = Thread(target=inventory)
    t1.start()
    health()
    sys.exit(0)
