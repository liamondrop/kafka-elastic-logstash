#!/usr/bin/env python

import math
import rospy
import tf, tf2_ros
import json
import pyproj
import avro.schema
from io import BytesIO
from avro.io import DatumWriter, DatumReader, BinaryEncoder, BinaryDecoder
from kafka import KafkaProducer
from kafka.errors import KafkaError
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import BrakeReport
from dbw_mkz_msgs.msg import SteeringReport
from dbw_mkz_msgs.msg import ThrottleReport

from requests_utils import request_retry_session

kafka_producer = KafkaProducer(bootstrap_servers=['172.18.0.1:9092'])

KAFKA_TOPIC = 'test-topic-2'
VEHICLE_SYSTEMS = ['brake', 'steering', 'throttle']

class VehicleClient:
    state = {
        'dbw_enabled': False,
        'brake_enabled': False,
        'steering_enabled': False,
        'throttle_enabled': False,
        'brake': {},
        'steering': {},
        'throttle': {},
        'lat': 0.,
        'lon': 0.,
        'angle': 0.,}

    def __init__(self):
        schema_file = rospy.get_param('~schema_file')
        with open(schema_file, 'rb') as fd:
            self.schema = avro.schema.parse(fd.read())

        self.config = None
        self.car_file = rospy.get_param('~car_file_name')
        self.car_name = rospy.get_param('~car_name')
        self.utm_zone = rospy.get_param('~utm_zone')
        self.web_app_uri = rospy.get_param('~web_app_uri')

        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.handle_dbw_enabled)
        rospy.Subscriber('/vehicle/brake_report', BrakeReport,
            self.handle_brake_report)
        rospy.Subscriber('/vehicle/steering_report', SteeringReport,
            self.handle_steering_report)
        rospy.Subscriber('/vehicle/throttle_report', ThrottleReport,
            self.handle_throttle_report)

    def load_config(self):
        try:
            with open(self.car_file) as fd:
                self.config = json.load(fd)
        except:
            rospy.logwarn('Vehicle not yet registered. Attempting to register')
            self.register_new()
        rospy.loginfo('Vehicle "{}" registered with cid {}'.format(
            self.car_name, self.config['cid']))

    def register_new(self):
        ses = request_retry_session(retries=None)
        res = ses.get('{}/new_car/{}'.format(
            self.web_app_uri, self.car_name))
        self.config = res.json()
        with open(self.car_file, 'w') as fd:
            json.dump(self.config, fd)

    def handle_dbw_enabled(self, msg):
        self.state['dbw_enabled'] = msg.data

    def handle_brake_report(self, msg):
        self.state['brake_enabled'] = msg.enabled
        self.state['brake'] = {
            'driver': msg.driver,
            'fault_ch1': msg.fault_ch1,
            'fault_ch2': msg.fault_ch2,
            'fault_power': msg.fault_power,
            'fault_wdc': msg.fault_wdc,
            'override': msg.override,
            'timeout': msg.timeout,}

    def handle_steering_report(self, msg):
        self.state['steering_enabled'] = msg.enabled
        self.state['steering'] = {
            'fault_bus1': msg.fault_bus1,
            'fault_bus2': msg.fault_bus2,
            'fault_calibration': msg.fault_calibration,
            'fault_power': msg.fault_power,
            'fault_wdc': msg.fault_wdc,
            'override': msg.override,
            'timeout': msg.timeout,}

    def handle_throttle_report(self, msg):
        self.state['throttle_enabled'] = msg.enabled
        self.state['throttle'] = {
            'driver': msg.driver,
            'fault_ch1': msg.fault_ch1,
            'fault_ch2': msg.fault_ch2,
            'fault_power': msg.fault_power,
            'fault_wdc': msg.fault_wdc,
            'override': msg.override,
            'timeout': msg.timeout,}

    def handle_pose_update(self, translation, rotation):
        easting, northing = translation[:2]
        utm_proj = pyproj.Proj(proj='utm', zone=self.utm_zone, ellps='WGS84')
        lon, lat = utm_proj(easting, northing, inverse=True)
        x, y, z = tf.transformations.euler_from_quaternion(rotation)
        self.state['lat'] = lat
        self.state['lon'] = lon
        self.state['angle'] = math.pi / 2. - z

    def is_autonomous(self):
        return (self.state['dbw_enabled'] and
                self.state['brake_enabled'] and
                self.state['steering_enabled'] and
                self.state['throttle_enabled'])

    def report(self):
        out = {
            'cid': self.config['cid'],
            'lat': self.state['lat'],
            'lon': self.state['lon'],
            'angle': self.state['angle'],}

        if (self.is_autonomous()):
            out['status'] = ''
            out['mode'] = 'A'
            return out

        status = {}
        for system in VEHICLE_SYSTEMS:
            if not self.state['{}_enabled'.format(system)]:
                status[system] = [
                    k for k,v in self.state[system].items() if v]
        out['status'] = json.dumps(status)
        out['mode'] = 'M'
        return out

    def serialize_status(self):
        status = self.report()
        writer = DatumWriter(self.schema)
        bytes_writer = BytesIO()
        encoder = BinaryEncoder(bytes_writer)
        writer.write(status, encoder)
        return bytes_writer.getvalue()
    
    def send_status(self, status):
        kafka_producer.send(KAFKA_TOPIC, status)


if __name__ == '__main__':
    rospy.init_node('vehicle_client')
    vehicle_client = VehicleClient()
    vehicle_client.load_config()
    listener = tf.TransformListener()
    tf_rate = rospy.get_param('~tf_rate')
    rate = rospy.Rate(tf_rate)
    while not rospy.is_shutdown():
        try:
            next_frame = rospy.Time(0)
            listener.waitForTransform('utm', 'base_link', next_frame,
                rospy.Duration(tf_rate))
            trans, rot = listener.lookupTransform('utm', 'base_link',
                next_frame)
        except (tf2_ros.TransformException, tf.LookupException,) as err:
            rospy.logwarn(err)
            continue

        vehicle_client.handle_pose_update(trans, rot)
        bytes_str = vehicle_client.serialize_status()
        vehicle_client.send_status(bytes_str)

        # deserialize
        bytes_reader = BytesIO(bytes_str)
        decoder = BinaryDecoder(bytes_reader)
        reader = DatumReader(vehicle_client.schema)
        decoded = reader.read(decoder)
        print decoded

        print("=" * 40)
        rate.sleep()

