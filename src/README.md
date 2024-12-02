# ATLAS Data Anslysis

CERN ATLAS experiment data analysis, focusing on the Hyy decay channel (Higgs boson to two photons). Implemented using a distributed scalable system using docker containers and kubernetes cluster management.

## Prerequisites

* Docker Desktop
* Kubernetes (enabled in Docker Desktop)
* kubectl CLI tool

## Installation

1. Install Docker Desktop for your operating system
2. Enable Kubernetes in Docker Desktop:
   * Open Docker Desktop settings
   * Navigate to Kubernetes tab
   * Check "Enable Kubernetes"
   * Wait for the installation to complete

## Verify Setup

```bash
# Verify Kubernetes installation
kubectl get nodes

# Verify Docker installation
docker container ls
```

## Clone the repository
```bash
git clone https://github.com/Lukelele/ATLASAnalysis
```

## Build the Docker image
```bash
cd src
docker build -t distributor HyyDistributor/.
docker build -t worker HyyWorker/.
docker build -t collector HyyCollector/.
```

## Alternatively, use docker-compose
```bash
cd src
docker-compose up
```

## Deploy to Kubernetes
```bash
cd src
kubectl apply -f deployment.yaml
```

## Manual Scaling with Kubernetes
```bash
kubectl scale --replicas=num_workers worker
```

## Automatic Scaling with Kubernetes
First install KEDA, then run
```bash
cd src
kubectl apply -f loadbalancer.yml
```
