#!/bin/bash

# deploy.sh - Script para preparar el volumen y desplegar con kustomize

echo "🚀 Iniciando despliegue..."

# Verificar que minikube esté corriendo
if ! minikube status > /dev/null 2>&1; then
    echo "❌ Minikube no está corriendo. Iniciando..."
    minikube start
fi

# Crear el directorio en minikube
echo "📁 Creando directorio /mnt/data en minikube..."
minikube ssh -- 'sudo mkdir -p /mnt/data && sudo chmod 777 /mnt/data'

# Aplicar kustomize
echo "⚙️ Aplicando configuración con kustomize..."
kubectl apply -k .

# Verificar el estado
echo "✅ Verificando PVC..."
kubectl get pvc -n hydroponics

echo "🎉 Despliegue completado!"