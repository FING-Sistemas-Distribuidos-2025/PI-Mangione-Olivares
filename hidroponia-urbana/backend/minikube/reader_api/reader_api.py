# Reader Backend - Flask API for querying sensor data
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
from bson import ObjectId
import json

# Configuration
MONGODB_URI = os.getenv('MONGODB_HEADLESS_SERVICE')
DATABASE_NAME = "hydroponics"
SENSOR_COLLECTION = "sensor_readings"
STATUS_COLLECTION = "node_status"


app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[DATABASE_NAME]
    sensor_collection = db[SENSOR_COLLECTION]
    status_collection = db[STATUS_COLLECTION]
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB ObjectId"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
    
# Sanitize MongoDB documents for JSON serialization
def sanitize_mongo_doc(doc):
    doc['_id'] = str(doc.get('_id'))
    
    # Convierte timestamp si es datetime
    if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
        doc['timestamp'] = doc['timestamp'].isoformat()
    elif 'timestamp' in doc:
        # Si es un float, lo convertimos a datetime primero
        try:
            doc['timestamp'] = datetime.utcfromtimestamp(doc['timestamp']).isoformat()
        except Exception:
            # Si no se puede convertir, lo dejamos como está
            pass
    return doc

app.json_encoder = JSONEncoder

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        mongo_client.admin.command('ping')
        return jsonify({
            "status": "healthy",
            "service": "reader_api",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get list of all active nodes"""
    try:
        # Get unique node IDs from recent data (last 24 hours)
        since = datetime.utcnow() - timedelta(hours=24)
        
        pipeline = [
            {"$match": {"server_timestamp": {"$gte": since}}},
            {"$group": {"_id": "$node_id", "last_seen": {"$max": "$server_timestamp"}}},
            {"$sort": {"last_seen": -1}}
        ]
        
        nodes = list(sensor_collection.aggregate(pipeline))
        
        return jsonify({
            "nodes": [{"node_id": node["_id"], "last_seen": node["last_seen"]} for node in nodes],
            "count": len(nodes)
        })
        
    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/last-values', methods=['GET'])
def get_last_values():
    """Get the most recent sensor values for all nodes or specific node"""
    try:
        node_id = request.args.get('node_id')
        
        # Build match criteria
        match_criteria = {}
        if node_id:
            match_criteria['node_id'] = node_id
        
        # Get the most recent reading for each node
        pipeline = [
            {"$match": match_criteria},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$node_id",
                "latest_reading": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_reading"}},
            {"$sort": {"timestamp": -1}}
        ]
        
        readings = list(sensor_collection.aggregate(pipeline))
        sanitized = [sanitize_mongo_doc(r) for r in readings]

        return jsonify({
            "readings": readings,
            "count": len(readings),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting last values: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get historical sensor data with filtering options"""
    try:
        # Parse query parameters
        node_id = request.args.get('node_id')
        sensor_type = request.args.get('sensor_type')  # temperature, humidity, ph, gas
        hours = int(request.args.get('hours', 24))  # Default last 24 hours
        limit = int(request.args.get('limit', 100))  # Default limit 100 records
        
        # Build query
        query = {}
        if node_id:
            query['node_id'] = node_id
        
        # Time range filter
        since = datetime.utcnow() - timedelta(hours=hours)
        query['server_timestamp'] = {"$gte": since}
        
        # Execute query
        cursor = sensor_collection.find(query).sort("timestamp", -1).limit(limit)
        readings = list(cursor)
        
        # Filter by sensor type if specified
        if sensor_type and readings:
            for reading in readings:
                if 'sensors' in reading and sensor_type in reading['sensors']:
                    # Keep only the requested sensor type
                    reading['sensors'] = {sensor_type: reading['sensors'][sensor_type]}
        
        # Sanitize readings
        sanitized_readings = [sanitize_mongo_doc(r) for r in readings]

        return jsonify({
            "readings": sanitized_readings,
            "count": len(sanitized_readings),
            "filters": {
                "node_id": node_id,
                "sensor_type": sensor_type,
                "hours": hours,
                "limit": limit
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return jsonify({"error": "Invalid parameter format"}), 400
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get statistical summary of sensor data"""
    try:
        node_id = request.args.get('node_id')
        hours = int(request.args.get('hours', 24))
        
        # Build match criteria
        match_criteria = {}
        if node_id:
            match_criteria['node_id'] = node_id
        
        # Time range filter
        since = datetime.utcnow() - timedelta(hours=hours)
        match_criteria['server_timestamp'] = {"$gte": since}
        
        # Aggregation pipeline for statistics
        pipeline = [
            {"$match": match_criteria},
            {"$group": {
                "_id": "$node_id",
                "count": {"$sum": 1},
                "avg_temperature": {"$avg": "$sensors.temperature"},
                "min_temperature": {"$min": "$sensors.temperature"},
                "max_temperature": {"$max": "$sensors.temperature"},
                "avg_humidity": {"$avg": "$sensors.humidity"},
                "min_humidity": {"$min": "$sensors.humidity"},
                "max_humidity": {"$max": "$sensors.humidity"},
                "avg_ph": {"$avg": "$sensors.ph"},
                "min_ph": {"$min": "$sensors.ph"},
                "max_ph": {"$max": "$sensors.ph"},
                "avg_gas": {"$avg": "$sensors.gas"},
                "min_gas": {"$min": "$sensors.gas"},
                "max_gas": {"$max": "$sensors.gas"},
                "first_reading": {"$min": "$server_timestamp"},
                "last_reading": {"$max": "$server_timestamp"}
            }}
        ]
        
        stats = list(sensor_collection.aggregate(pipeline))
        
        return jsonify({
            "statistics": stats,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return jsonify({"error": "Invalid parameter format"}), 400
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get sensor readings that exceed normal thresholds"""
    try:
        hours = int(request.args.get('hours', 24))
        
        # Define alert thresholds
        thresholds = {
            "temperature": {"min": 15, "max": 30},
            "humidity": {"min": 30, "max": 90},
            "ph": {"min": 5.0, "max": 8.0},
            "gas": {"min": 200, "max": 1000}
        }
        
        # Time range filter
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Build query for out-of-range values
        alert_conditions = []
        for sensor, limits in thresholds.items():
            alert_conditions.extend([
                {f"sensors.{sensor}": {"$lt": limits["min"]}},
                {f"sensors.{sensor}": {"$gt": limits["max"]}}
            ])
        
        query = {
            "server_timestamp": {"$gte": since},
            "$or": alert_conditions
        }
        
        alerts = list(sensor_collection.find(query).sort("timestamp", -1).limit(50))
        
        # Add alert type to each reading
        for alert in alerts:
            alert['alert_types'] = []
            if 'sensors' in alert:
                for sensor, value in alert['sensors'].items():
                    if sensor in thresholds:
                        limits = thresholds[sensor]
                        if value < limits["min"]:
                            alert['alert_types'].append(f"{sensor}_low")
                        elif value > limits["max"]:
                            alert['alert_types'].append(f"{sensor}_high")
        
        return jsonify({
            "alerts": alerts,
            "count": len(alerts),
            "thresholds": thresholds,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return jsonify({"error": "Invalid parameter format"}), 400
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
