import os
import time
import logging
import avro.schema
from io import BytesIO
from avro.io import DatumWriter, BinaryEncoder
from kafka import KafkaProducer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_URI = '{}:9092'.format(os.environ['KAFKA_HOST'])
KAFKA_TOPIC = os.environ['KAFKA_TOPIC']
SCHEMA_PATH = '/usr/share/schema.avsc'

def value_serializer(msg):
    writer = DatumWriter(schema)
    bytes_writer = BytesIO()
    encoder = BinaryEncoder(bytes_writer)
    writer.write(msg, encoder)
    return bytes_writer.getvalue()

if __name__ == '__main__':
    with open(SCHEMA_PATH, 'rb') as fd:
        schema = avro.schema.parse(fd.read())

    kafka_producer = KafkaProducer(
        bootstrap_servers=[KAFKA_URI],
        value_serializer=value_serializer
    )

    for i in range(10):
        msg = {
            'name': 'test',
            'value': i,
            'description': 'The value is {}'.format(i)
        }
        kafka_producer.send(KAFKA_TOPIC, msg)
        logging.info('Sent msg: {}'.format(msg))

    kafka_producer.flush()
