ARG ELK_VERSION

FROM docker.elastic.co/logstash/logstash:${ELK_VERSION}

RUN logstash-plugin install logstash-codec-avro
