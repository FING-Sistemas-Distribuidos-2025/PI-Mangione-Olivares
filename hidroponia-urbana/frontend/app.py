import os
from venv import logger
from flask import Flask, render_template, jsonify
import random
from datetime import datetime, timedelta

import requests

app = Flask(__name__)

# Configuration
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://reader-api-service.hydroponics.svc.cluster.local:5001')

'''
def generate_sample_data():
    data = []
    labels = []
    current_time = datetime.now() - timedelta(hours=23) 

    for i in range(24): 
        time_label = (current_time + timedelta(hours=i)).strftime("%H:%M")
        labels.append(time_label)

       
        temperatura = round(random.uniform(18.0, 25.0), 2)
        humedad = round(random.uniform(40.0, 60.0), 2)
        presion = round(random.uniform(980.0, 1020.0), 2)
        consumo_energia = round(random.uniform(0.5, 3.0), 2)

        data.append({
            "time": time_label,
            "temperatura": temperatura,
            "humedad": humedad,
            "presion": presion,
            "consumo_energia": consumo_energia
        })
    return labels, data
'''

def calculate_statistics(data):
    stats = {}
    if not data:
        return stats

    
    temps = [d["temperatura"] for d in data]
    humids = [d["humedad"] for d in data]
    pressures = [d["presion"] for d in data]
    energies = [d["consumo_energia"] for d in data]

    stats["temperatura"] = {
        "min": min(temps),
        "max": max(temps),
        "avg": round(sum(temps) / len(temps), 2),
        "std_dev": round((sum([(x - (sum(temps) / len(temps)))**2 for x in temps]) / len(temps))**0.5, 2)
    }
    stats["humedad"] = {
        "min": min(humids),
        "max": max(humids),
        "avg": round(sum(humids) / len(humids), 2),
        "std_dev": round((sum([(x - (sum(humids) / len(humids)))**2 for x in humids]) / len(humids))**0.5, 2)
    }
    stats["presion"] = {
        "min": min(pressures),
        "max": max(pressures),
        "avg": round(sum(pressures) / len(pressures), 2),
        "std_dev": round((sum([(x - (sum(pressures) / len(pressures)))**2 for x in pressures]) / len(pressures))**0.5, 2)
    }
    stats["consumo_energia"] = {
        "min": min(energies),
        "max": max(energies),
        "avg": round(sum(energies) / len(energies), 2),
        "std_dev": round((sum([(x - (sum(energies) / len(energies)))**2 for x in energies]) / len(energies))**0.5, 2)
    }

    return stats


chart_labels, sensor_data = 0,0 
statistics_data = calculate_statistics(sensor_data)


@app.route('/')
def index():
    """Ruta principal que renderiza la página de inicio."""
    return render_template('index.html', stats=statistics_data, sensor_data_json=sensor_data)

'''
def get_data():
    """API endpoint para obtener los datos de las medidas y estadísticas."""
    return jsonify({
        "labels": chart_labels,
        "measures": sensor_data,
        "statistics": statistics_data
    })
'''
@app.route('/api/data')
def get_data():
    try:
        # Llama a la API del reader
        response = requests.get(f"{BACKEND_API_URL}/api/last-values", timeout=5)
        data = response.json()

        readings = data.get("readings", [])

        # Inicializamos listas
        chart_labels = []
        sensor_data = {
            "temperature": [],
            "humidity": [],
            "ph": [],
            "gas": []
        }

        # Iteramos sobre cada lectura
        for reading in readings:
            ts = reading.get("timestamp")
            chart_labels.append(ts)

            sensors = reading.get("sensors", {})
            sensor_data["temperature"].append(sensors.get("temperature"))
            sensor_data["humidity"].append(sensors.get("humidity"))
            sensor_data["ph"].append(sensors.get("ph"))
            sensor_data["gas"].append(sensors.get("gas"))

        return jsonify({
            "labels": chart_labels,
            "data": sensor_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history')
def get_history():
    try:
        # Llama a la API del reader
        response = requests.get(f"{BACKEND_API_URL}/api/history", timeout=5)
        data = response.json()

        readings = data.get("readings", [])

        # Inicializamos listas 
        node_id = []
        chart_labels = []
        sensor_data = {
            "temperature": [],
            "humidity": [],
            "ph": [],
            "gas": []
        }

        # Iteramos sobre cada lectura
        for reading in readings:
            node_id.append(reading.get("node_id"))
            ts = reading.get("timestamp")
            chart_labels.append(ts)

            sensors = reading.get("sensors", {})
            sensor_data["temperature"].append(sensors.get("temperature"))
            sensor_data["humidity"].append(sensors.get("humidity"))
            sensor_data["ph"].append(sensors.get("ph"))
            sensor_data["gas"].append(sensors.get("gas"))

        return jsonify({
            "node_id": node_id,
            "labels": chart_labels,
            "data": sensor_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
