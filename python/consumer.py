import os
import logging
import avro.schema
from io import BytesIO
from avro.io import DatumReader, BinaryDecoder
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_URI = '{}:{}'.format(
    os.environ['KAFKA_HOST'], os.environ['KAFKA_PORT'])
KAFKA_TOPIC = os.environ['KAFKA_TOPIC']
SCHEMA_PATH = '/usr/share/schema.avsc'

def value_deserializer(msg):
    bytes_reader = BytesIO(msg)
    decoder = BinaryDecoder(bytes_reader)
    reader = DatumReader(schema)
    return reader.read(decoder)

if __name__ == '__main__':
    with open(SCHEMA_PATH, 'rb') as fd:
        schema = avro.schema.parse(fd.read())

    kafka_consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_URI],
        value_deserializer=value_deserializer
    )

    for msg in kafka_consumer:
        logger.info("Received msg: {}:{}:{}: key={} value={}".format(
            msg.topic, msg.partition, msg.offset, msg.key, msg.value))
