import configparser, sys
from loguru import logger
from pathlib import Path

from models.orm_dnac import DataBase
from modules.DNA_health import DNAHealth

class DNA():
    def __init__(self):
        # Load configuration form conf.cnf file
        cnf_file = Path(__file__).resolve().parent.parent.joinpath('conf.cnf')

        config_path = cnf_file
        config = configparser.ConfigParser()
        config.readfp(open(config_path))
        self.dnac_url = config.get('dnac', 'url')
        self.usr = config.get('dnac', 'usr')
        self.passwd = config.get('dnac', 'passwd')
        self.db_path = config.get('dna_database', 'db_path')
        self.DNA = None

        # Default LogLevel
        LOGLEVEL = config.get('logger', 'LOGLEVEL')
        LOGFILE = config.get('logger', 'LOGFILE')

        # logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>", level="INFO")
        # logger.propagate = False
        # config = {
        #     "handlers": [
        #         {"sink": LOGFILE, 'level': LOGLEVEL, 'rotation':"01:00"},
        #     ]
        # }
        # logger.configure(**config)
        # logger.add(LOGFILE, level=LOGLEVEL, rotation="01:00")


    def dna_connect(self):
        DNAHealth(self.dnac_url, self.usr, self.passwd)
        self.DNA = DNAHealth(self.dnac_url, self.usr, self.passwd)

class DNAGetInventory(DNA):

    def get_inventory(self, db):
        logger.info('Starting getting inventory process')
        self.DNA.getDevices(db)


    # if __name__ == "__main__":
    def run(self):
        self.dna_connect()
        db = DataBase(self.db_path)
        db.create_tables()
        self.get_inventory(db)
        # self.aci.logout()


class DNAGetHealth(DNA):

    def get_health(self, db):
        logger.info('Starting getting healthy process')
        self.DNA.getNodesHelath(db)
        
    def get_issues(self,db):
        logger.info('Starting getting issues process')
        self.DNA.getIssues(db)

    def run(self):
        self.dna_connect()
        db = DataBase(self.db_path)
        db.create_tables()
        self.get_health(db)
        self.get_issues(db)
        # self.aci.logout()

