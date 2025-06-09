# ESP32 Simulator - Python version for testing in Docker
import json
import time
import random
import os
import logging
from datetime import datetime
import paho.mqtt.client as mqtt

# Configuration from environment variables
NODE_ID = os.getenv('NODE_ID', 'node_001')
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=f'%(asctime)s - {NODE_ID} - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ESP32Simulator:
    def __init__(self):
        self.mqtt_client = None
        self.connected = False
        self.irrigation_active = False
        
    def generate_sensor_data(self):
        """Generate random sensor data simulating real sensors"""
        # Add some realistic variations
        base_temp = 22.0 + random.uniform(-3, 5)
        base_humidity = 60.0 + random.uniform(-15, 20)
        base_ph = 6.5 + random.uniform(-1, 1)
        base_gas = 400 + random.uniform(-100, 200)
        
        return {
            "node_id": NODE_ID,
            "timestamp": time.time(),
            "sensors": {
                "temperature": round(base_temp, 2),
                "humidity": round(base_humidity, 2),
                "ph": round(base_ph, 2),
                "gas": round(base_gas, 0)
            },
            "status": "active",
            "irrigation_active": self.irrigation_active
        }
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to control topics
            control_topic = f"control/riego/{NODE_ID}"
            broadcast_topic = "control/riego/broadcast"
            
            client.subscribe(control_topic)
            client.subscribe(broadcast_topic)
            
            logger.info(f"Subscribed to {control_topic} and {broadcast_topic}")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            message = json.loads(msg.payload.decode('utf-8'))
            
            logger.info(f"Received message on {topic}: {message}")
            
            # Handle irrigation commands
            if topic.endswith(NODE_ID) or topic.endswith("broadcast"):
                self.handle_irrigation_command(message)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def handle_irrigation_command(self, command):
        """Handle irrigation control commands"""
        try:
            action = command.get("action")
            duration = command.get("duration", 5)
            
            if action == "activate":
                logger.info(f"Activating irrigation for {duration} seconds")
                self.irrigation_active = True
                self.send_status_update("irrigation_started", duration)
                
                # Simulate irrigation duration
                time.sleep(duration)
                self.irrigation_active = False
                self.send_status_update("irrigation_completed", duration)
                
            elif action == "deactivate":
                logger.info("Deactivating irrigation")
                self.irrigation_active = False
                self.send_status_update("irrigation_stopped")
                
        except Exception as e:
            logger.error(f"Error handling irrigation command: {e}")
    
    def send_status_update(self, action, duration=None):
        """Send status update to MQTT broker"""
        try:
            status_msg = {
                "node_id": NODE_ID,
                "action": action,
                "timestamp": time.time(),
                "irrigation_active": self.irrigation_active
            }
            
            if duration:
                status_msg["duration"] = duration
            
            topic = f"status/{NODE_ID}"
            message = json.dumps(status_msg)
            
            self.mqtt_client.publish(topic, message)
            logger.info(f"Status update sent: {action}")
            
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
    
    def publish_sensor_data(self):
        """Publish sensor data to MQTT broker"""
        try:
            sensor_data = self.generate_sensor_data()
            topic = f"sensor/data/{NODE_ID}"
            message = json.dumps(sensor_data)
            
            self.mqtt_client.publish(topic, message)
            logger.info(f"Published sensor data: {sensor_data['sensors']}")
            
        except Exception as e:
            logger.error(f"Error publishing sensor data: {e}")
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_message = self.on_message
            
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 30
            while not self.connected and timeout > 0:
                time.sleep(1)
                timeout -= 1
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def run(self):
        """Main execution loop"""
        logger.info(f"Starting ESP32 Simulator: {NODE_ID}")
        
        # Connect to MQTT
        if not self.connect_mqtt():
            logger.error("Cannot proceed without MQTT connection")
            return
        
        logger.info("ESP32 simulator initialized successfully!")
        
        # Main loop
        last_sensor_publish = 0
        sensor_interval = 600  #seconds
        
        try:
            while True:
                current_time = time.time()
                
                # Publish sensor data every 30 seconds
                if current_time - last_sensor_publish >= sensor_interval:
                    self.publish_sensor_data()
                    last_sensor_publish = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down ESP32 simulator...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()

def main():
    """Main function"""
    simulator = ESP32Simulator()
    simulator.run()

if __name__ == "__main__":
    main()
