import logging

logger = logging.getLogger('monitor_exporter')

class ExporterLog:

    def start():
        logging.basicConfig(filename='monitor_exporter.log', level=logging.INFO)

    def error(message):
        logger.error('description|{}'.format(message))

    def info(message):
       logger.info('description|{}'.format(message))