from kafka import KafkaConsumer
import avro.schema
from io import BytesIO
from avro.io import DatumReader, BinaryDecoder

KAFKA_TOPIC = 'test-topic-2'

schema_file = '/home/liam/.ros/schema.avsc'
with open(schema_file, 'rb') as fd:
    schema = avro.schema.parse(fd.read())

def value_deserializer(m):
    bytes_reader = BytesIO(m)
    decoder = BinaryDecoder(bytes_reader)
    reader = DatumReader(schema)
    return reader.read(decoder)

# To consume latest messages and auto-commit offsets
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=['172.18.0.1:9092'],
    value_deserializer=value_deserializer
)

print KAFKA_TOPIC

for message in consumer:
    # message value and key are raw bytes -- decode if necessary!
    # e.g., for unicode: `message.value.decode('utf-8')`
    # deserialize
    print ("%s:%d:%d: key=%s" % (message.topic, message.partition,
                                 message.offset, message.key))
    print '-' * 40
    print message.value
    print '=' * 40
