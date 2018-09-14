import avro.schema
from io import BytesIO
from avro.io import DatumWriter, BinaryEncoder
from kafka import KafkaProducer
from kafka.errors import KafkaError

KAFKA_TOPIC = 'test-topic-2'

schema_file = '/home/liam/.ros/schema.avsc'
with open(schema_file, 'rb') as fd:
    schema = avro.schema.parse(fd.read())

def value_serializer(msg):
    writer = DatumWriter(schema)
    bytes_writer = BytesIO()
    encoder = BinaryEncoder(bytes_writer)
    writer.write(msg, encoder)
    return bytes_writer.getvalue()

kafka_producer = KafkaProducer(
    bootstrap_servers=['172.18.0.1:9092'],
    value_serializer=value_serializer
)
