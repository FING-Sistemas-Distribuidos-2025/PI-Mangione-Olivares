from flask import Flask, render_template, jsonify
import random
from datetime import datetime, timedelta

app = Flask(__name__)


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


chart_labels, sensor_data = generate_sample_data()
statistics_data = calculate_statistics(sensor_data)


@app.route('/')
def index():
    """Ruta principal que renderiza la página de inicio."""
    return render_template('index.html', stats=statistics_data, sensor_data_json=sensor_data)

@app.route('/api/data')
def get_data():
    """API endpoint para obtener los datos de las medidas y estadísticas."""
    return jsonify({
        "labels": chart_labels,
        "measures": sensor_data,
        "statistics": statistics_data
    })

if __name__ == '__main__':
    app.run(debug=True)
