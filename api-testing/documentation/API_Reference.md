# Medical Research AI - API Reference

Complete API documentation for the Medical Research AI voice-to-voice medical consultation system.

## Base URL

```
http://localhost:8000
```

## Authentication

No authentication required for local development/testing environment.

---

## Health & Monitoring Endpoints

### GET /health

Check the overall health status of the Medical Research AI system.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-25T22:35:00Z",
  "voice_interface": {
    "tts_loaded": true,
    "asr_available": true,
    "model_loaded": true
  },
  "resilience": {
    "circuit_breakers_active": true,
    "retry_policies_enabled": true
  },
  "model_info": {
    "name": "google/flan-t5-base",
    "device": "mps",
    "dtype": "float32"
  }
}
```

### GET /api/resilience/status

Get current resilience patterns status including circuit breaker states and failure rates.

**Response:**
```json
{
  "circuit_breakers": {
    "asr_circuit_breaker": {
      "state": "closed",
      "failure_count": 0,
      "last_failure": null
    },
    "tts_circuit_breaker": {
      "state": "closed", 
      "failure_count": 0,
      "last_failure": null
    }
  },
  "retry_policies": {
    "asr_retry_policy": {
      "max_attempts": 3,
      "current_failures": 0
    },
    "tts_retry_policy": {
      "max_attempts": 3,
      "current_failures": 0
    }
  }
}
```

### WebSocket /ws/health

Real-time health monitoring via WebSocket connection.

**Connection:** `ws://localhost:8000/ws/health`

**Messages Received:**
```json
{
  "type": "health_update",
  "timestamp": "2025-08-25T22:35:00Z",
  "status": "healthy",
  "voice_interface_status": "operational",
  "resilience_status": "active"
}
```

---

## Medical Consultation Endpoints

### POST /api/consultation/text

Perform a text-based medical consultation using the google/flan-t5-base model.

**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symptoms` | string | Yes | Patient's symptom description |
| `patient_age` | integer | No | Patient's age |
| `patient_gender` | string | No | Patient's gender |
| `medical_history` | string | No | Comma-separated medical history |

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/consultation/text \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "symptoms=I have severe chest pain radiating to my left arm, shortness of breath, and I'm sweating profusely" \
  -d "patient_age=55" \
  -d "patient_gender=male" \
  -d "medical_history=hypertension,diabetes"
```

**Response:**
```json
{
  "success": true,
  "consultation_id": "consult_abc123",
  "analysis": {
    "urgency": "emergency",
    "confidence": 0.95,
    "is_emergency": true,
    "recommendations": [
      "Call 911 immediately",
      "Do not drive yourself to hospital",
      "Chew aspirin if not allergic"
    ],
    "red_flags": [
      "Chest pain with radiation",
      "Shortness of breath", 
      "Diaphoresis"
    ],
    "patient_friendly_response": "Based on your symptoms of severe chest pain radiating to your left arm, shortness of breath, and sweating, this appears to be a medical emergency that requires immediate attention. These symptoms could indicate a heart attack. Please call 911 immediately and do not attempt to drive yourself to the hospital.",
    "model_used": "google/flan-t5-base"
  },
  "processing_time_ms": 1250
}
```

### POST /api/consultation/voice

Perform a voice-based medical consultation with audio file upload.

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audio_file` | file | Yes | Audio file (.wav, .mp3, .m4a, .flac) |
| `patient_age` | integer | No | Patient's age |
| `patient_gender` | string | No | Patient's gender |
| `medical_history` | string | No | Comma-separated medical history |

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/consultation/voice \
  -F "audio_file=@patient_symptoms.wav" \
  -F "patient_age=45" \
  -F "patient_gender=female" \
  -F "medical_history=asthma,allergies"
```

**Response:**
```json
{
  "success": true,
  "consultation_id": "consult_voice_xyz789",
  "transcription": "I have severe chest pain radiating to my left arm and shortness of breath",
  "analysis": {
    "urgency": "emergency",
    "confidence": 0.92,
    "is_emergency": true,
    "recommendations": [
      "Seek immediate emergency care",
      "Call 911 or go to nearest emergency room"
    ],
    "red_flags": [
      "Chest pain with radiation",
      "Shortness of breath"
    ],
    "patient_friendly_response": "Your symptoms suggest a serious condition that requires immediate medical attention. Please seek emergency care right away.",
    "model_used": "google/flan-t5-base"
  },
  "has_audio_response": true,
  "processing_time_ms": 3450
}
```

---

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

---

## Error Responses

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "symptoms"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Internal Server Error (500):**
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "Model inference failed"
}
```

---

## Data Models

### Urgency Levels

| Level | Description |
|-------|-------------|
| `emergency` | Immediate medical attention required |
| `high` | Urgent medical attention needed |
| `moderate` | Medical attention recommended |
| `low` | Routine care or self-care appropriate |

### Medical Response Structure

```json
{
  "urgency": "emergency",
  "confidence": 0.95,
  "is_emergency": true,
  "recommendations": ["Array of recommendation strings"],
  "red_flags": ["Array of concerning symptoms"],
  "patient_friendly_response": "Human-readable explanation",
  "model_used": "google/flan-t5-base"
}
```

---

## Rate Limits

No rate limits currently implemented for local development environment.

## Audio File Requirements

### Supported Formats
- WAV (recommended)
- MP3
- M4A  
- FLAC

### Specifications
- **Sample Rate:** 16kHz recommended (8kHz - 48kHz supported)
- **Channels:** Mono preferred (stereo supported)
- **Duration:** Maximum 5 minutes
- **File Size:** Maximum 50MB

---

## Model Information

### Current Model: google/flan-t5-base

- **Parameters:** 990M
- **Architecture:** Text-to-Text Transfer Transformer
- **Capabilities:** Medical reasoning, symptom analysis, urgency assessment
- **Language:** English
- **Device:** Auto-detected (MPS on Mac, CUDA on GPU systems, CPU fallback)

---

## WebSocket Events

### Health Monitoring WebSocket

**Connection:** `ws://localhost:8000/ws/health`

**Event Types:**

1. **health_update** - Periodic health status
2. **voice_interface_status** - Voice component status changes
3. **resilience_update** - Circuit breaker state changes

**Message Format:**
```json
{
  "type": "event_type",
  "timestamp": "ISO8601_timestamp",
  "data": { /* event-specific data */ }
}
```

---

## Development Notes

- Server runs on port 8000 by default
- Uses FastAPI framework with automatic OpenAPI documentation
- Real-time health monitoring via WebSocket
- Resilience patterns implemented (circuit breakers, retry policies)
- Production-ready architecture with dependency injection
