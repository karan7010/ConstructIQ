# AI-Assisted Construction Planning and Resource Intelligence System

A full-stack cloud platform for optimized construction project management, material estimation, and resource tracking.

## 🏗️ System Architecture

- **Flutter Mobile App**: Site engineers (logs) & Project Managers (dashboards).
- **Firebase Backend**: Auth, Firestore (Real-time DB), Storage (CAD files), Cloud Functions.
- **Python Microservice**: CAD/DXF parsing, Estimation engine, ML Cost Overrun prediction, RAG AI.

## 📁 Repository Structure

- `/construction-flutter-app`: Flutter source code, styling, and Firebase integration.
  - `/functions`: Firebase Cloud Functions (Node.js).
- `/construction-ai-service`: Python FastAPI microservice logic.

## 🚀 Getting Started

### Python Microservice
1. `cd construction-ai-service`
2. `python -m venv venv`
3. `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. `pip install -r requirements.txt`
5. `uvicorn main:app --reload`

### Flutter App
1. `cd construction_flutter_app`
2. `flutter pub get`
3. Configure Firebase using `flutterfire configure`
4. `flutter run`

## 🛠️ Tech Stack

- **Frontend**: Flutter, Riverpod, GoRouter, fl_chart.
- **Backend**: Firebase (Auth, Firestore, Storage, Functions).
- **AI/ML**: FastAPI, ezdxf, XGBoost, LangChain, ChromaDB, Gemini 1.5 Flash.
