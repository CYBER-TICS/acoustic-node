# Acoustic AI Node / Nodo de IA Acústica

## Español

### Descripción

**Acoustic AI Node** es un proyecto de clasificación acústica basado en Python, diseñado para entrenar un modelo capaz de distinguir entre sonido ambiente y un sonido objetivo de drone shahead usando archivos de audio `.wav`.

En esta primera etapa, el sistema:

* organiza audios por clases,
* extrae características acústicas,
* entrena un modelo de machine learning,
* y realiza predicciones sobre nuevos audios.

Más adelante, el proyecto podrá evolucionar hacia:

* detección en tiempo real con micrófono,
* ejecución en Raspberry Pi,
* despliegue como nodo autónomo,
* y envío de alertas.

---

### Objetivo

Construir una base sólida para un sistema de reconocimiento acústico que permita detectar un sonido objetivo dentro de ruido ambiental.

---

### Estado actual del proyecto

Actualmente el proyecto incluye:

* preparación de datos de audio,
* extracción de features,
* entrenamiento de un modelo,
* predicción sobre archivos nuevos.

---

### Estructura del proyecto

```
acoustic-ai-node/
│
├── data/
│   ├── train/
│   │   ├── ambiente/
│   │   └── motor_objetivo/
│   ├── test/
│   │   ├── ambiente/
│   │   └── motor_objetivo/
│   └── predict/
│
├── models/
├── src/
│   ├── prepare_data.py
│   ├── train_model.py
│   ├── predict.py
│   └── main.py
│
├── config/
├── logs/
├── scripts/
├── systemd/
├── requirements.txt
├── .gitignore
└── README.md
```

---

### Requisitos

* Python 3.10 o superior
* pip
* Visual Studio Code recomendado

---

### Instalación

```
pip install -r requirements.txt
```

---

### Dependencias principales

* numpy
* librosa
* scikit-learn
* joblib
* soundfile

---

### Organización de datos

Los audios deben almacenarse en formato `.wav`.

#### Entrenamiento

* `data/train/ambiente/`
* `data/train/motor_objetivo/`

#### Pruebas

* `data/test/ambiente/`
* `data/test/motor_objetivo/`

#### Predicción

* `data/predict/`

---

### Flujo de trabajo

#### 1. Preparar dataset

Colocar audios en las carpetas correspondientes.

#### 2. Entrenar el modelo

```
python src/train_model.py
```

#### 3. Ejecutar predicción

```
python src/predict.py
```

---

### Salida esperada

```
Archivo: ejemplo.wav
Clase predicha: motor_objetivo
Confianza: 0.87
⚠️ ALERTA: sonido objetivo detectado
```

o

```
Archivo: ejemplo.wav
Clase predicha: ambiente
Confianza: 0.91
✅ Sonido ambiente normal
```

---

### Próximos pasos

* aumentar dataset de entrenamiento
* mejorar calidad y variedad de audios
* evaluar precisión del modelo
* incorporar grabación por micrófono
* implementar inferencia en tiempo real
* preparar despliegue en Raspberry Pi

---

### Notas

Este proyecto se encuentra en fase temprana de prototipo.
La calidad del modelo dependerá directamente de la calidad, cantidad y diversidad del dataset de audio.

---

## English

### Description

**Acoustic AI Node** is a Python-based acoustic classification project designed to train a model capable of distinguishing between background sound and a target drone shahead motor sound using `.wav` audio files.

At this first stage, the system:

* organizes audio samples by class,
* extracts acoustic features,
* trains a machine learning model,
* and performs predictions on new audio files.

Later, the project may evolve into:

* real-time microphone detection
* Raspberry Pi deployment
* autonomous field node execution
* alert generation

---

### Objective

Build a solid foundation for an acoustic recognition system able to detect a target sound in noisy environments.

---

### Current project status

The project currently includes:

* audio data preparation
* feature extraction
* model training
* prediction on new audio files

---

### Project structure

```
acoustic-ai-node/
│
├── data/
│   ├── train/
│   │   ├── ambiente/
│   │   └── motor_objetivo/
│   ├── test/
│   │   ├── ambiente/
│   │   └── motor_objetivo/
│   └── predict/
│
├── models/
├── src/
│   ├── prepare_data.py
│   ├── train_model.py
│   ├── predict.py
│   └── main.py
│
├── config/
├── logs/
├── scripts/
├── systemd/
├── requirements.txt
├── .gitignore
└── README.md
```

---

### Requirements

* Python 3.10 or higher
* pip
* Visual Studio Code recommended

---

### Installation

```
pip install -r requirements.txt
```

---

### Main dependencies

* numpy
* librosa
* scikit-learn
* joblib
* soundfile

---

### Data organization

Audio files should be stored in `.wav` format.

#### Training

* `data/train/ambiente/`
* `data/train/motor_objetivo/`

#### Testing

* `data/test/ambiente/`
* `data/test/motor_objetivo/`

#### Prediction

* `data/predict/`

---

### Workflow

#### 1. Prepare dataset

Place audio files into the corresponding folders.

#### 2. Train the model

```
python src/train_model.py
```

#### 3. Run prediction

```
python src/predict.py
```

---

### Expected output

```
Archivo: ejemplo.wav
Clase predicha: motor_objetivo
Confianza: 0.87
⚠️ ALERTA: sonido objetivo detectado
```

or

```
Archivo: ejemplo.wav
Clase predicha: ambiente
Confianza: 0.91
✅ Sonido ambiente normal
```

---

### Next steps

* expand the training dataset
* improve audio quality and diversity
* evaluate model accuracy
* add microphone input
* implement real-time inference
* prepare Raspberry Pi deployment

---

### Notes

This project is currently in an early prototype stage.
Model quality will strongly depend on the quality, quantity, and diversity of the audio dataset.
