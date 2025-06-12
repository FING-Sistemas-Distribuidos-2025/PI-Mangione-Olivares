# MQTT Writer Backend - Subscribes to sensor data and stores in MongoDB
import os
import json
import time
import logging
from datetime import datetime
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Configuration
#MQTT_BROKER = "localhost"
MQTT_BROKER = os.getenv('MQTT_BROKER')
#MQTT_PORT = 1883
MQTT_PORT = int(os.getenv('MQTT_PORT'))
MQTT_TOPICS = ["sensor/data/#", "status/#"]

#MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = "hydroponics"
SENSOR_COLLECTION = "sensor_readings"
STATUS_COLLECTION = "node_status"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MQTTWriterService:
    def __init__(self):
        self.mqtt_client = None
        self.mongo_client = None
        self.db = None
        self.sensor_collection = None
        self.status_collection = None
        
    def connect_mongodb(self):
        """Connect to MongoDB database"""
        try:
            self.mongo_client = MongoClient(MONGODB_URI)
            # Test connection
            self.mongo_client.admin.command('ping')
            
            self.db = self.mongo_client[DATABASE_NAME]
            self.sensor_collection = self.db[SENSOR_COLLECTION]
            self.status_collection = self.db[STATUS_COLLECTION]
            
            # Create indexes for better query performance
            self.sensor_collection.create_index([("node_id", 1), ("timestamp", -1)])
            self.status_collection.create_index([("node_id", 1), ("timestamp", -1)])
            
            logger.info("Connected to MongoDB successfully")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            # Subscribe to all configured topics
            for topic in MQTT_TOPICS:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            logger.info(f"Received message on topic {topic}")
            
            # Route message based on topic
            if topic.startswith("sensor/data/"):
                self.store_sensor_data(payload)
            elif topic.startswith("status/"):
                self.store_status_data(payload)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def store_sensor_data(self, data):
        """Store sensor data in MongoDB"""
        try:
            # Add server timestamp
            data['server_timestamp'] = datetime.utcnow()
            data['processed_at'] = time.time()
            
            # Validate required fields
            required_fields = ['node_id', 'timestamp', 'sensors']
            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in sensor data: {data}")
                return
            
            # Insert into MongoDB
            result = self.sensor_collection.insert_one(data)
            logger.info(f"Stored sensor data from node {data['node_id']} with ID: {result.inserted_id}")
            
        except OperationFailure as e:
            logger.error(f"Failed to store sensor data in MongoDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error storing sensor data: {e}")
    
    def store_status_data(self, data):
        """Store node status data in MongoDB"""
        try:
            # Add server timestamp
            data['server_timestamp'] = datetime.utcnow()
            data['processed_at'] = time.time()
            
            # Insert into MongoDB
            result = self.status_collection.insert_one(data)
            logger.info(f"Stored status data from node {data.get('node_id', 'unknown')} with ID: {result.inserted_id}")
            
        except OperationFailure as e:
            logger.error(f"Failed to store status data in MongoDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error storing status data: {e}")
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_message = self.on_message
            
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def run(self):
        """Start the writer service"""
        logger.info("Starting MQTT Writer Service...")
        
        # Connect to MongoDB
        if not self.connect_mongodb():
            logger.error("Cannot start service without MongoDB connection")
            return
        
        # Connect to MQTT
        if not self.connect_mqtt():
            logger.error("Cannot start service without MQTT connection")
            return
        
        logger.info("Writer service started successfully")
        
        try:
            # Start MQTT loop
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down writer service...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            if self.mqtt_client:
                self.mqtt_client.disconnect()
            if self.mongo_client:
                self.mongo_client.close()

def main():
    """Main function"""
    service = MQTTWriterService()
    service.run()

if __name__ == "__main__":
    main()
