# 🚀 Quick Start Guide - Enhanced Medical Research AI

Get up and running with the Enhanced Medical Research AI system in under 5 minutes!

## ⚡ Super Quick Start (1 minute)

```bash
# Clone and install (Linux/macOS)
git clone <repository-url>
cd medical_research
./install.sh

# Or on Windows
install.bat

# Start the server
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python web/main.py

# Open browser to http://localhost:8000
```

## 📋 Prerequisites Checklist

- [ ] **Python 3.9+** installed
- [ ] **4GB+ RAM** available
- [ ] **2GB+ storage** for AI models
- [ ] **Internet connection** for model downloads

## 🎯 Step-by-Step Installation

### 1. Install Dependencies

#### Option A: Automated Installation (Recommended)
```bash
# Linux/macOS
./install.sh

# Windows
install.bat
```

#### Option B: Manual Installation
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-web.txt

# Download AI models
python download_models.py
```

### 2. Start the Server

```bash
# Activate environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Start web server
python web/main.py
```

### 3. Test the System

Open your browser to: **http://localhost:8000**

## 🧪 Quick Tests

### Test 1: Basic Text Consultation
1. Go to http://localhost:8000
2. Enter symptoms: "I have fever and headache for 2 days"
3. Fill patient details (age: 30, gender: male)
4. Click "Analyze Symptoms"
5. ✅ Should get diagnosis with drug recommendations

### Test 2: Enhanced Consultation
1. Use the "Enhanced Consultation" form
2. Enter: "severe stomach pain and nausea"
3. ✅ Should get interactive follow-up questions

### Test 3: API Endpoint
```bash
curl -X POST "http://localhost:8000/api/consultation/enhanced" \
  -F "symptoms=chest pain and difficulty breathing" \
  -F "patient_age=45" \
  -F "patient_gender=female"
```

## 🔧 Configuration

### Basic Configuration (.env file)
```bash
# Enhanced features
ENABLE_DRUG_RECOMMENDATIONS=true
ENABLE_INTERACTIVE_DIAGNOSIS=true

# Model settings
MEDICAL_MODEL=google/flan-t5-base
MEDICAL_DEVICE=auto
```

### Performance Tuning

#### For Low-Memory Systems (< 8GB RAM)
```bash
export MEDICAL_MODEL=google/flan-t5-small
export FORCE_TORCH_DTYPE=float32
export MEDICAL_DEVICE=cpu
```

#### For High-Performance Systems (16GB+ RAM)
```bash
export MEDICAL_MODEL=google/flan-t5-large
export MEDICAL_DEVICE=cuda  # If GPU available
```

## 🩺 Key Features to Test

### 1. Enhanced Diagnosis
- **Multi-backend AI**: More accurate than basic models
- **Confidence scoring**: Reliability metrics for each diagnosis
- **Medical knowledge**: Integrated medical databases

### 2. Interactive Questioning
- **Progressive questions**: System asks follow-up questions
- **Smart adaptation**: Questions adapt based on your answers
- **Session management**: Maintains context across interactions

### 3. Indian Healthcare Context
- **Local medications**: Indian brand names (Crocin, Dolo, Brufen)
- **INR pricing**: Costs in Indian Rupees (₹2-25 per tablet)
- **Safety checks**: Age-appropriate dosing and warnings
- **Availability**: Local pharmacy availability scoring

### 4. Drug Recommendations
| Condition | Recommended Drugs | Indian Brands | Cost (INR) |
|-----------|------------------|---------------|------------|
| Fever | Paracetamol | Crocin, Dolo | ₹2-8 |
| Pain | Ibuprofen | Brufen, Combiflam | ₹3-12 |
| Cold | Vitamin C | Limcee, Celin | ₹1-5 |

## 🚨 Troubleshooting

### Common Issues

#### "Model not found" error
```bash
# Download models manually
python download_models.py
```

#### "Port 8000 already in use"
```bash
# Use different port
python web/main.py --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9  # Linux/macOS
netstat -ano | findstr :8000   # Windows
```

#### Slow response times
```bash
# Use smaller model
export MEDICAL_MODEL=google/flan-t5-small

# Force CPU usage
export MEDICAL_DEVICE=cpu
```

#### Memory issues
```bash
# Reduce memory usage
export FORCE_TORCH_DTYPE=float32
export MEDICAL_DEVICE=cpu
```

### Getting Help

1. **Check logs**: Look at console output for error messages
2. **Restart server**: Stop and restart `python web/main.py`
3. **Clear cache**: Delete `~/.cache/huggingface/` folder
4. **Check requirements**: Ensure all dependencies are installed

## 🎯 Next Steps

### 1. Explore Advanced Features
- Try voice consultation with audio files
- Test the interactive diagnosis flow
- Explore drug interaction checking

### 2. API Integration
- Use the REST API endpoints
- Import the Insomnia collection from `api-testing/`
- Build your own client applications

### 3. Customization
- Add more Indian medications to the database
- Configure Infermedica API for enhanced accuracy
- Customize the web interface

### 4. Production Deployment
```bash
# Install production dependencies
pip install gunicorn

# Run with gunicorn
gunicorn web.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📚 Documentation

- **Full README**: [README.md](README.md)
- **Enhanced System Details**: [docs/ENHANCED_MEDICAL_DIAGNOSIS_SYSTEM.md](docs/ENHANCED_MEDICAL_DIAGNOSIS_SYSTEM.md)
- **API Testing**: [api-testing/README.md](api-testing/README.md)
- **API Documentation**: http://localhost:8000/docs (when server is running)

## ✅ Success Checklist

- [ ] Server starts without errors
- [ ] Web interface loads at http://localhost:8000
- [ ] Basic text consultation works
- [ ] Enhanced consultation provides drug recommendations
- [ ] Interactive diagnosis asks follow-up questions
- [ ] API endpoints respond correctly

**🎉 Congratulations! Your Enhanced Medical Research AI system is ready to provide comprehensive medical consultations with Indian healthcare context!**

---

**Need help?** Check the troubleshooting section above or refer to the full documentation in README.md
