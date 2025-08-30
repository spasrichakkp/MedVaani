# Medical Research AI - Insomnia Collection Summary

## 🎯 Collection Overview

The **Medical Research AI Collection** is a comprehensive Insomnia REST client collection designed for testing and validating the Medical Research AI voice-to-voice medical consultation system. This collection provides immediate access to all API endpoints with pre-configured test scenarios.

## 📦 What's Included

### 1. **Complete Insomnia Collection** (`Medical_Research_AI_Collection.json`)
- **5 Core Endpoints** organized into logical groups
- **Environment Variables** for easy configuration
- **Multiple Test Scenarios** for different medical urgency levels
- **Proper Headers and Content Types** pre-configured
- **Sample Data** for immediate testing

### 2. **Organized Endpoint Groups**

#### 🏥 **Health & Monitoring**
- **Health Check** - System status and component health
- **Resilience Status** - Circuit breaker and retry policy monitoring  
- **WebSocket Health Monitor** - Real-time health updates

#### 💬 **Medical Consultations**
- **Text Consultation - Emergency Cardiac** - High-urgency test case
- **Text Consultation - Moderate Symptoms** - Medium-urgency test case
- **Text Consultation - Mild Symptoms** - Low-urgency test case
- **Voice Consultation** - Audio file upload with medical analysis

### 3. **Sample Test Data**
- **8 Medical Scenarios** covering emergency to routine cases
- **3 Sample Audio Files** for voice consultation testing
- **Expected Response Examples** for validation
- **Audio File Generator Script** for creating custom test files

### 4. **Comprehensive Documentation**
- **API Reference** with detailed endpoint specifications
- **Setup Instructions** for immediate use
- **Troubleshooting Guide** for common issues
- **Performance Benchmarks** and expected response times

## 🚀 Quick Import & Test

### Step 1: Import Collection
1. Open Insomnia REST Client
2. File → Import/Export → Import Data
3. Select `insomnia-collections/Medical_Research_AI_Collection.json`
4. Collection appears with all endpoints ready to use

### Step 2: Verify Server
Ensure your Medical Research AI server is running:
```bash
# Server should be running on http://localhost:8000
curl http://localhost:8000/health
```

### Step 3: Test Endpoints
Start with the **Health Check** endpoint to verify connectivity, then proceed to test medical consultations.

## 🔬 Test Scenarios Included

| Scenario | Symptoms | Expected Urgency | Use Case |
|----------|----------|------------------|----------|
| **Emergency Cardiac** | Chest pain, arm radiation, SOB | Emergency | Critical care validation |
| **Respiratory Distress** | Breathing difficulty, wheezing | High | Urgent care testing |
| **Neurological Emergency** | Stroke-like symptoms | Emergency | Emergency detection |
| **Moderate Fever** | Persistent fever, body aches | Moderate | Standard care flow |
| **Mild Cold** | Headache, runny nose | Low | Routine consultation |
| **Pediatric Emergency** | Child breathing difficulty | Emergency | Pediatric scenarios |
| **Mental Health Crisis** | Self-harm thoughts | Emergency | Mental health handling |
| **Chronic Condition** | Arthritis flare-up | Moderate | Chronic care management |

## 📊 Validation Checklist

### ✅ **API Functionality**
- [ ] Health endpoint returns comprehensive status
- [ ] Text consultations process successfully
- [ ] Voice consultations accept audio uploads
- [ ] Resilience monitoring shows circuit breaker states
- [ ] WebSocket connections establish properly

### ✅ **Medical Analysis Quality**
- [ ] Emergency symptoms correctly identified
- [ ] Appropriate urgency levels assigned
- [ ] Relevant recommendations provided
- [ ] Red flags properly detected
- [ ] Patient-friendly responses generated

### ✅ **System Performance**
- [ ] Response times within expected ranges
- [ ] Model shows "google/flan-t5-base"
- [ ] Error handling works correctly
- [ ] File uploads process successfully

## 🎯 **Current Test Results**

**✅ API Connectivity**: All endpoints responding correctly  
**✅ Health Monitoring**: Comprehensive system status available  
**✅ Voice Interface**: Audio upload and processing functional  
**✅ Resilience Patterns**: Circuit breakers and retry policies active  
**⚠️ Model Accuracy**: Some urgency classification needs refinement  

## 🔧 **Environment Configuration**

The collection uses these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `base_url` | `http://localhost:8000` | API server base URL |

**To modify**: Insomnia → Environment dropdown → Manage Environments → Edit values

## 📁 **File Structure Reference**

```
api-testing/
├── insomnia-collections/
│   └── Medical_Research_AI_Collection.json    # 🎯 Main collection file
├── sample-data/
│   ├── test_scenarios.json                    # Test case definitions
│   ├── sample_patient_symptoms.wav            # Audio test files
│   ├── emergency_symptoms.wav
│   ├── routine_checkup.wav
│   └── create_sample_audio.py                 # Audio generator
├── documentation/
│   └── API_Reference.md                       # Complete API docs
├── README.md                                  # Setup instructions
└── COLLECTION_SUMMARY.md                     # This file
```

## 🏆 **Ready for Production Testing**

This collection provides everything needed to:
- **Validate API functionality** across all endpoints
- **Test medical reasoning** with realistic scenarios  
- **Monitor system health** and resilience patterns
- **Verify voice processing** pipeline end-to-end
- **Benchmark performance** against expected metrics

**Import the collection and start testing immediately!** 🚀

---

**Collection Version**: 1.0  
**Compatible with**: Medical Research AI v1.0+  
**Last Updated**: August 25, 2025  
**Insomnia Format**: v4
