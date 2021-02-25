import configparser, sys
from loguru import logger
from modules.ACI_health import ACIHealt
from models.orm_aci import DataBase
from pathlib import Path

class AciInventory():
    def __init__(self):
        # Load configuration form conf.cnf file
        cnf_file = Path(__file__).resolve().parent.parent.joinpath('conf.cnf')

        config_path = cnf_file
        config = configparser.ConfigParser()
        config.readfp(open(config_path))
        self.apic_url = config.get('apic', 'apic_url')
        self.usr = config.get('apic', 'usr')
        self.passwd = config.get('apic', 'passwd')
        self.db_path = config.get('database', 'db_path')

        # Default LogLevel
        LOGLEVEL = config.get('logger', 'LOGLEVEL')
        LOGFILE = config.get('logger', 'LOGFILE')

        # logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>", level="INFO")
        logger.propagate = False
        config = {
            "handlers": [
                {"sink": LOGFILE, 'level': LOGLEVEL, 'rotation':"01:00"},
            ]
        }
        logger.configure(**config)
        # logger.add(LOGFILE, level=LOGLEVEL, rotation="01:00")

        self.aci = None

    def aci_connect(self):
        self.aci = ACIHealt(self.apic_url, self.usr, self.passwd)

    def get_inventory(self, db):
        logger.info('Starting getting inventory process')
        self.aci.refresh_token()
        self.aci.getTenants(db)
        self.aci.getNodes(db)
        self.aci.getAppAndBDList(db)
        self.aci.getEpgList(db)


    # if __name__ == "__main__":
    def run(self):
        self.aci_connect()
        db = DataBase(self.db_path)
        db.create_tables()
        self.get_inventory(db)
        self.aci.logout()


class AciHealth():
    def __init__(self):
        # Load configuration form conf.cnf file
        cnf_file = Path(__file__).resolve().parent.parent.joinpath('conf.cnf')

        config_path = cnf_file
        config = configparser.ConfigParser()
        config.readfp(open(config_path))
        self.apic_url = config.get('apic', 'apic_url')
        self.usr = config.get('apic', 'usr')
        self.passwd = config.get('apic', 'passwd')
        self.db_path = config.get('database', 'db_path')

        # Default LogLevel
        LOGLEVEL = config.get('logger', 'LOGLEVEL')
        LOGFILE = config.get('logger', 'LOGFILE')

        # logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>", level="INFO")
        logger.propagate = False
        config = {
            "handlers": [
                {"sink": LOGFILE, 'level': LOGLEVEL, 'rotation': "01:00"},
            ]
        }
        logger.configure(**config)

        self.aci = None

    def aci_connect(self):
        self.aci = ACIHealt(self.apic_url, self.usr, self.passwd)

    def get_health(self, db):
        logger.info('Starting getting healthy process')
        self.aci.refresh_token()
        self.aci.getTenantHealth(db)
        self.aci.getNodesHelath(db)
        self.aci.getAppHealth(db)
        self.aci.getBdHealth(db)
        self.aci.getEpgHelath(db)
        self.aci.getFaultsSummary(db)


    # if __name__ == "__main__":
    def run(self):
        self.aci_connect()
        db = DataBase(self.db_path)
        db.create_tables()
        self.get_health(db)
        self.aci.logout()

