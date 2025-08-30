# 🩺 Enhanced Medical Research AI

A comprehensive voice-to-voice medical consultation system with enhanced diagnostic accuracy, interactive questioning, and Indian healthcare-specific drug recommendations.

## 🎯 Project Overview

This system transforms basic medical consultations into comprehensive, interactive healthcare guidance specifically designed for the Indian population. It features:

- **🔬 Enhanced Diagnostic Accuracy**: Multi-backend AI approach with medical knowledge bases
- **💬 Interactive Diagnosis**: Progressive questioning to refine diagnosis accuracy
- **💊 Indian Drug Recommendations**: Local brand names, pricing in INR, and availability
- **📊 Real-time Progress Tracking**: User feedback during longer processing times
- **🌐 Web Interface**: Modern FastAPI + HTMX interface for easy access
- **🗣️ Voice Support**: Complete voice-to-voice consultation pipeline

## 🏗️ System Architecture

```
Web Interface (FastAPI + HTMX)
    ↓
Enhanced Medical Services
    ├── Interactive Diagnosis Service
    ├── Progress Tracking Service
    ├── Drug Recommendation Service
    └── Enhanced Medical Adapter
        ├── Infermedica API (optional)
        ├── Clinical Knowledge Graph
        ├── RxNorm Integration
        └── Fallback Medical Models
```

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.9+ (3.11+ recommended)
- **System Memory**: 4GB+ RAM
- **Storage**: 2GB+ free space for models
- **OS**: Windows, macOS, or Linux

### Installation

#### Option 1: Using UV (Recommended)

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup project
git clone <repository-url>
cd medical_research

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uv pip install -r requirements-web.txt
```

#### Option 2: Using pip

```bash
# Clone project
git clone <repository-url>
cd medical_research

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-web.txt
```

### Environment Setup

Create a `.env` file in the project root (optional):

```bash
# Optional: Infermedica API for enhanced accuracy
INFERMEDICA_APP_ID=your_app_id
INFERMEDICA_APP_KEY=your_app_key

# Enhanced features (enabled by default)
ENABLE_DRUG_RECOMMENDATIONS=true
ENABLE_INTERACTIVE_DIAGNOSIS=true

# Model configuration
MEDICAL_MODEL=google/flan-t5-base
MEDICAL_DEVICE=auto
ENVIRONMENT=development
```

## 🎮 Running the Application

### Development Mode

```bash
# Start the web server
python web/main.py

# Or using uvicorn directly
uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
# Using gunicorn for production
gunicorn web.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Access the Application

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### Core Endpoints

#### Enhanced Medical Consultation
```bash
curl -X POST "http://localhost:8000/api/consultation/enhanced" \
  -F "symptoms=I have severe headache and fever for 2 days" \
  -F "patient_age=30" \
  -F "patient_gender=male"
```

#### Interactive Diagnosis
```bash
# Start interactive session
curl -X POST "http://localhost:8000/api/diagnosis/interactive/start" \
  -F "symptoms=chest pain and shortness of breath"

# Answer follow-up questions
curl -X POST "http://localhost:8000/api/diagnosis/interactive/answer" \
  -F "session_id=abc123" \
  -F "question_id=pain_severity" \
  -F "answer=8"
```

#### Voice Consultation
```bash
curl -X POST "http://localhost:8000/api/consultation/voice" \
  -F "audio_file=@symptoms.wav" \
  -F "patient_age=25" \
  -F "patient_gender=female"
```

### System Endpoints

- `GET /health` - System health check
- `GET /api/resilience/status` - Resilience patterns status
- `WebSocket /ws/health` - Real-time health monitoring

## 🧪 Testing

### Run Unit Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/test_domain_entities.py
pytest tests/test_phase2_integration.py
```

### Test API Endpoints
```bash
# Test basic functionality
python test_api_endpoints.py

# Test voice interface
python test_voice_interface.py

# Test enhanced medical consultation
python test_meerkat_diagnosis.py
```

### Manual Testing

1. **Web Interface**: Visit http://localhost:8000 and test both text and voice input
2. **Enhanced Consultation**: Use the enhanced consultation form for better accuracy
3. **Interactive Diagnosis**: Try the interactive questioning feature
4. **Drug Recommendations**: Check Indian medication suggestions with pricing

## 🔧 Configuration

### Optional Services

#### Infermedica API (Enhanced Accuracy)
1. Sign up at [Infermedica Developer Portal](https://developer.infermedica.com/)
2. Get your App ID and App Key
3. Set environment variables:
   ```bash
   export INFERMEDICA_APP_ID=your_app_id
   export INFERMEDICA_APP_KEY=your_app_key
   ```

#### Model Configuration
```yaml
# configs/models.yaml
models:
  enhanced_medical:
    name: "google/flan-t5-base"
    device: "auto"
    precision: "float32"
```

### Performance Tuning

#### For Low-Memory Systems
```bash
export MEDICAL_MODEL=google/flan-t5-small
export FORCE_TORCH_DTYPE=float32
```

#### For High-Performance Systems
```bash
export MEDICAL_MODEL=google/flan-t5-large
export MEDICAL_DEVICE=cuda
```

## 🩺 Medical Features

### Enhanced Diagnosis
- **Multi-Backend Analysis**: Combines multiple AI systems for better accuracy
- **Confidence Scoring**: Provides reliability metrics for each diagnosis
- **Interactive Refinement**: Follow-up questions improve diagnostic accuracy

### Indian Healthcare Context
- **Local Medications**: 7+ common drugs with Indian brand names
- **INR Pricing**: Cost estimates in Indian Rupees (₹2-25 per tablet)
- **Safety Checks**: Age-appropriate dosing and contraindication warnings
- **Availability Scoring**: Local pharmacy availability considerations

### Drug Recommendations
| Generic Name | Indian Brands | Category | Cost Range (INR) |
|--------------|---------------|----------|------------------|
| Paracetamol | Crocin, Dolo, Calpol | Antipyretic | ₹2-8 per tablet |
| Ibuprofen | Brufen, Combiflam | Analgesic | ₹3-12 per tablet |
| Amoxicillin | Novamox, Moxikind | Antibiotic | ₹5-15 per capsule |
| Vitamin C | Limcee, Celin | Vitamin | ₹1-5 per tablet |

## 🔍 Troubleshooting

### Common Issues

#### Model Loading Errors
```bash
# Clear model cache
rm -rf ~/.cache/huggingface/

# Download models manually
python download_models.py
```

#### Memory Issues
```bash
# Use smaller model
export MEDICAL_MODEL=google/flan-t5-small

# Force CPU usage
export MEDICAL_DEVICE=cpu
```

#### Port Already in Use
```bash
# Use different port
uvicorn web.main:app --port 8001

# Kill existing process
lsof -ti:8000 | xargs kill -9
```

#### Dependencies Issues
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Update to latest versions
pip install --upgrade -r requirements.txt
```

### Performance Issues

#### Slow Response Times
1. Check system resources: `htop` or Task Manager
2. Use smaller model: `export MEDICAL_MODEL=google/flan-t5-small`
3. Enable GPU if available: `export MEDICAL_DEVICE=cuda`

#### High Memory Usage
1. Restart the application periodically
2. Use CPU-only mode: `export MEDICAL_DEVICE=cpu`
3. Reduce batch sizes in model configuration

## 📚 Documentation

- **Enhanced System Overview**: [docs/ENHANCED_MEDICAL_DIAGNOSIS_SYSTEM.md](docs/ENHANCED_MEDICAL_DIAGNOSIS_SYSTEM.md)
- **API Testing Collection**: [api-testing/README.md](api-testing/README.md)
- **API Documentation**: http://localhost:8000/docs (when server is running)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing issues in the repository
3. Create a new issue with detailed information about your problem

---

**🇮🇳 Built for Indian Healthcare - Accessible, Accurate, and Affordable Medical AI**
