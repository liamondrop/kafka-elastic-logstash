import os
import logging
import avro.schema
from io import BytesIO
from avro.io import DatumReader, BinaryDecoder
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_HOST = os.environ['KAFKA_HOST']
KAFKA_TOPIC = os.environ['KAFKA_TOPIC']
CWD = os.path.dirname(os.path.realpath(__file__))
SCHEMA_PATH = os.path.join(CWD, 'schema', os.environ['SCHEMA_FILE'])

def value_deserializer(msg):
    bytes_reader = BytesIO(msg)
    decoder = BinaryDecoder(bytes_reader)
    reader = DatumReader(schema)
    return reader.read(decoder)

if __name__ == '__main__':
    print(KAFKA_TOPIC, KAFKA_HOST)

    with open(SCHEMA_PATH, 'rb') as fd:
        schema = avro.schema.parse(fd.read())

    kafka_consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=['{}:9092'.format(KAFKA_HOST)],
        value_deserializer=value_deserializer
    )

    for msg in kafka_consumer:
        logger.info("{}:{}:{}: key={}".format(
            msg.topic, msg.partition, msg.offset, msg.key))
        logger.info("msg={}".format(msg.value))
