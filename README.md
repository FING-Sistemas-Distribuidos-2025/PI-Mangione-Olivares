# PI-Hidroponia - Sistema IoT para Hidroponía Urbana

Sistema distribuido de monitoreo y control para hidroponía urbana utilizando ESP32, MQTT, MongoDB y Kubernetes.

## 🌱 Características

- **Monitoreo en tiempo real** de sensores (temperatura, humedad, pH, gases)
- **Control remoto de riego** a través de interfaz web
- **Escalabilidad horizontal** con Kubernetes
- **Dashboard web interactivo** con gráficos en tiempo real
- **Comunicación MQTT** para IoT
- **Base de datos MongoDB** para almacenamiento de datos

## 🏗️ Arquitectura del Sistema

![Arquitectura](images/arq_sist.png)

## 🚀 Instalación y Despliegue

### Prerrequisitos

- Docker y Docker Compose
- Kubernetes cluster (minikube, k3s, etc.)
- kubectl configurado
- ESP32 con MicroPython (para nodos físicos)

## 🔧 Configuración

### Variables de Entorno

#### Backend
- `MONGODB_URI`: URI de conexión a MongoDB
- `MQTT_BROKER`: Dirección del broker MQTT
- `MQTT_PORT`: Puerto del broker MQTT (default: 1883)
- `DATABASE_NAME`: Nombre de la base de datos

#### Frontend
- `BACKEND_API_URL`: URL del API backend

#### ESP32
- `WIFI_SSID`: Nombre de la red WiFi
- `WIFI_PASSWORD`: Contraseña de la red WiFi
- `MQTT_BROKER`: Dirección IP del broker MQTT
- `NODE_ID`: Identificador único del nodo

## 📊 API Endpoints

### Backend API (Puerto 5000)

- `GET /api/nodes` - Lista de nodos activos
- `GET /api/sensor-data` - Datos de sensores más recientes
- `GET /api/history` - Datos históricos
- `GET /api/statistics` - Estadísticas del sistema
- `POST /api/irrigation` - Control de riego

## 📈 Monitoreo

### Métricas Disponibles

- Número de nodos activos
- Frecuencia de lecturas de sensores
- Tiempo de respuesta del API
- Uso de recursos (CPU, memoria)
