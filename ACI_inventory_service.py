import configparser, sys
from loguru import logger
from modules.ACI_health import ACIHealt
from models.orm_aci import DataBase

aci = None
def ACI():
    global aci
    aci = ACIHealt(apic_url, usr, passwd)

def get_inventory():
    logger.info('Starting getting inventory process')
    aci.refresh_token()
    aci.getTenants(db)
    aci.getNodes(db)
    aci.getAppAndBDList(db)
    aci.getEpgList(db)


if __name__ == "__main__":
    # Load configuration form conf.cnf file
    cnf_file = 'conf.cnf'

    config_path = cnf_file
    config = configparser.ConfigParser()
    config.readfp(open(config_path))
    apic_url = config.get('apic', 'apic_url')
    usr = config.get('apic', 'usr')
    passwd = config.get('apic', 'passwd')
    db_path = config.get('database', 'db_path')

    # Default LogLevel
    LOGLEVEL = config.get('logger', 'LOGLEVEL')
    LOGFILE = config.get('logger', 'LOGFILE')

    logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>", level="INFO" )
    logger.add(LOGFILE, level=LOGLEVEL, rotation="01:00")

    ACI()

    db = DataBase(db_path)
    db.create_tables()
    get_inventory()
    aci.logout()

