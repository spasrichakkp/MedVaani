# Medical Research AI - API Testing Suite

This directory contains a comprehensive API testing suite for the Enhanced Medical Research AI system with interactive diagnosis, drug recommendations, and Indian healthcare context. The suite includes Insomnia REST client collections, sample test data, and documentation for easy API verification.

## 📁 Directory Structure

```
api-testing/
├── insomnia-collections/
│   └── Medical_Research_AI_Collection.json    # Main Insomnia collection
├── sample-data/
│   ├── test_scenarios.json                    # Test cases and expected responses
│   ├── sample_patient_symptoms.wav            # Sample audio for voice consultation
│   ├── emergency_symptoms.wav                 # Emergency scenario audio
│   ├── routine_checkup.wav                    # Routine consultation audio
│   └── create_sample_audio.py                 # Script to generate test audio files
├── documentation/
│   └── API_Reference.md                       # Detailed API documentation
└── README.md                                  # This file
```

## 🚀 Quick Start

### 1. Import Insomnia Collection

1. Open Insomnia REST Client
2. Click "Import/Export" → "Import Data"
3. Select `insomnia-collections/Medical_Research_AI_Collection.json`
4. The collection will be imported with all endpoints and environment variables

### 2. Start the Medical Research AI Server

```bash
cd medical_research/web
source ../.venv/bin/activate
export ENVIRONMENT=production
export MEDICAL_MODEL=google/flan-t5-base
export MEDICAL_DEVICE=auto
export FORCE_TORCH_DTYPE=float32
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Test the Endpoints

The collection includes the following organized endpoint groups:

#### Health & Monitoring
- **Health Check** (GET /health)
- **Resilience Status** (GET /api/resilience/status)
- **WebSocket Health Monitor** (WS /ws/health)

#### Enhanced Medical Consultations
- **Enhanced Consultation** (POST /api/consultation/enhanced) - Multi-backend AI with drug recommendations
- **Interactive Diagnosis Start** (POST /api/diagnosis/interactive/start) - Begin interactive questioning
- **Interactive Diagnosis Answer** (POST /api/diagnosis/interactive/answer) - Answer follow-up questions

#### Medical Consultations
- **Text Consultation** (POST /api/consultation/text)
- **Voice Consultation** (POST /api/consultation/voice)

## 🔧 Environment Configuration

The collection uses environment variables for easy configuration:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000` | Base URL for the Medical Research AI API |

To modify the environment:
1. In Insomnia, click the environment dropdown (top-left)
2. Select "Manage Environments"
3. Edit the "Base Environment" values as needed

## 📋 Test Scenarios

The `sample-data/test_scenarios.json` file contains comprehensive test cases:

### Emergency Scenarios
- **Cardiac Emergency**: Chest pain with radiation, shortness of breath
- **Respiratory Distress**: Severe breathing difficulties, wheezing
- **Neurological Emergency**: Stroke-like symptoms
- **Mental Health Crisis**: Self-harm thoughts, severe anxiety

### Routine Scenarios  
- **Moderate Symptoms**: Persistent fever, body aches
- **Mild Symptoms**: Headache, runny nose
- **Chronic Condition**: Arthritis flare-up

### Voice Consultation Testing
- Sample WAV files for different scenarios
- Multiple audio formats supported (.wav, .mp3, .m4a, .flac)
- Test transcription accuracy and medical analysis

## 🎯 Expected API Responses

### Successful Text Consultation
```json
{
  "success": true,
  "consultation_id": "consult_abc123",
  "analysis": {
    "urgency": "emergency",
    "confidence": 0.95,
    "is_emergency": true,
    "recommendations": ["Call 911 immediately"],
    "red_flags": ["Chest pain with radiation"],
    "patient_friendly_response": "Based on your symptoms...",
    "model_used": "google/flan-t5-base"
  },
  "processing_time_ms": 1250
}
```

### Successful Voice Consultation
```json
{
  "success": true,
  "consultation_id": "consult_voice_xyz789",
  "transcription": "I have severe chest pain",
  "analysis": { /* same as text consultation */ },
  "has_audio_response": true,
  "processing_time_ms": 3450
}
```

## 🔍 Testing Checklist

### Health Endpoints
- [ ] Health check returns comprehensive status
- [ ] Resilience status shows circuit breaker states
- [ ] WebSocket connection establishes and receives updates

### Text Consultation
- [ ] Emergency symptoms correctly identified as high urgency
- [ ] Appropriate medical recommendations provided
- [ ] Red flags properly detected
- [ ] Patient-friendly responses generated
- [ ] Model shows "google/flan-t5-base"

### Voice Consultation  
- [ ] Audio file upload successful
- [ ] Transcription generated (placeholder or real)
- [ ] Medical analysis performed on transcribed text
- [ ] Audio response generated
- [ ] Processing time reasonable (<60 seconds)

## 🛠️ Troubleshooting

### Common Issues

**Server Not Responding**
- Verify server is running on port 8000
- Check environment variables are set correctly
- Ensure virtual environment is activated

**Voice Consultation Errors**
- Verify audio file format is supported
- Check file size (should be reasonable for upload)
- Ensure patient demographics are properly formatted

**Model Loading Issues**
- Confirm google/flan-t5-base model is downloaded
- Check available disk space and memory
- Verify TORCH_DTYPE compatibility with your system

### Debug Commands

```bash
# Check server health
curl http://localhost:8000/health

# Test text consultation
curl -X POST http://localhost:8000/api/consultation/text \
  -d "symptoms=test&patient_age=30"

# Check server logs
# (View terminal where uvicorn is running)
```

## 📊 Performance Benchmarks

Expected performance metrics:

| Endpoint | Expected Response Time | Notes |
|----------|----------------------|-------|
| Health Check | < 100ms | Simple status check |
| Text Consultation | 1-3 seconds | Model inference time |
| Voice Consultation | 10-30 seconds | Includes transcription + TTS |
| Resilience Status | < 200ms | Circuit breaker status |

## 🔐 Security Considerations

- This is a development/testing environment
- No authentication required for local testing
- Do not use real patient data in testing
- Audio files are processed locally (not sent to external services)

## 📝 Contributing

To add new test scenarios:

1. Add test cases to `sample-data/test_scenarios.json`
2. Create corresponding audio files if needed
3. Update this README with new scenarios
4. Test the new scenarios in Insomnia

---

**Ready to Test!** 🚀

Import the collection into Insomnia and start testing the Medical Research AI API endpoints. The collection provides a complete testing environment for verifying all functionality we've implemented and improved during development.
