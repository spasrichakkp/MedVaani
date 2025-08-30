"""FastAPI web application for Medical Research AI system."""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from infrastructure.config.dependency_injection import ApplicationContainer
from application.use_cases.voice_consultation_use_case import VoiceConsultationUseCase
from application.use_cases.medical_analysis_use_case import MedicalAnalysisUseCase
from domain.value_objects.medical_symptoms import MedicalSymptoms
from domain.entities.patient import Patient
from infrastructure.logging.logger_factory import get_module_logger

# Import enhanced services
from infrastructure.adapters.enhanced_medical_adapter import EnhancedMedicalAdapter
from application.services.interactive_diagnosis_service import InteractiveDiagnosisService
from application.services.progress_tracking_service import ProgressTrackingService, ProgressStage
from application.services.drug_recommendation_service import DrugRecommendationService

# Initialize FastAPI app
app = FastAPI(
    title="Medical Research AI",
    description="Voice-to-voice medical consultation system",
    version="1.0.0"
)

# Setup static files and templates
web_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=web_dir / "static"), name="static")
templates = Jinja2Templates(directory=web_dir / "templates")

# Initialize application container
container = ApplicationContainer()

# Initialize logger factory
from infrastructure.logging.logger_factory import LoggerFactory
from infrastructure.logging.log_config import LogConfig

log_config = LogConfig()
LoggerFactory.initialize(log_config)
logger = get_module_logger(__name__)

# WebSocket connections for health monitoring
active_connections: Dict[str, WebSocket] = {}

# Progress tracking helper functions
async def broadcast_progress_update(consultation_id: str, step: str, progress: float, message: str, estimated_time: str = None):
    """Broadcast progress update to all connected WebSocket clients."""
    progress_data = {
        "type": "consultation_progress",
        "data": {
            "consultation_id": consultation_id,
            "step": step,
            "progress": progress,
            "message": message,
            "estimated_time": estimated_time,
            "timestamp": asyncio.get_event_loop().time()
        }
    }

    # Send to all active connections
    disconnected_connections = []
    for connection_id, websocket in active_connections.items():
        try:
            await websocket.send_json(progress_data)
        except Exception as e:
            logger.warning(f"Failed to send progress update to connection {connection_id}: {e}")
            disconnected_connections.append(connection_id)

    # Clean up disconnected connections
    for connection_id in disconnected_connections:
        active_connections.pop(connection_id, None)

async def broadcast_diagnosis_complete(consultation_id: str, results: dict, confidence: float, urgency: str):
    """Broadcast diagnosis completion to all connected WebSocket clients."""
    completion_data = {
        "type": "diagnosis_complete",
        "data": {
            "consultation_id": consultation_id,
            "results": results,
            "confidence": confidence,
            "urgency": urgency,
            "timestamp": asyncio.get_event_loop().time()
        }
    }

    # Send to all active connections
    disconnected_connections = []
    for connection_id, websocket in active_connections.items():
        try:
            await websocket.send_json(completion_data)
        except Exception as e:
            logger.warning(f"Failed to send completion update to connection {connection_id}: {e}")
            disconnected_connections.append(connection_id)

    # Clean up disconnected connections
    for connection_id in disconnected_connections:
        active_connections.pop(connection_id, None)

# Enhanced services
enhanced_medical_adapter: Optional[EnhancedMedicalAdapter] = None
interactive_diagnosis_service: Optional[InteractiveDiagnosisService] = None
progress_tracking_service: Optional[ProgressTrackingService] = None
drug_recommendation_service: Optional[DrugRecommendationService] = None


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    global enhanced_medical_adapter, interactive_diagnosis_service, progress_tracking_service, drug_recommendation_service

    logger.info("Starting Medical Research AI web application")
    container.initialize()

    # Initialize enhanced services
    enhanced_medical_adapter = EnhancedMedicalAdapter(
        enable_drug_recommendations=True,
        enable_interactive_diagnosis=True
    )

    interactive_diagnosis_service = InteractiveDiagnosisService(enhanced_medical_adapter)
    progress_tracking_service = ProgressTrackingService()
    drug_recommendation_service = DrugRecommendationService()

    # Warm up the enhanced medical adapter
    await enhanced_medical_adapter.warm_up_model()

    logger.info("Enhanced medical services initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global enhanced_medical_adapter

    logger.info("Shutting down Medical Research AI web application")

    # Cleanup enhanced services
    if enhanced_medical_adapter:
        await enhanced_medical_adapter.close()

    # Container cleanup if needed


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main consultation interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/enhanced", response_class=HTMLResponse)
async def enhanced_consultation(request: Request):
    """Enhanced consultation interface with real-time progress tracking."""
    return templates.TemplateResponse("enhanced_consultation.html", {"request": request})


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint."""
    try:
        voice_interface = container.get_voice_interface()
        health_status = await voice_interface.get_health_status()
        
        return {
            "status": "healthy",
            "voice_interface": health_status,
            "timestamp": health_status.get("timestamp", "unknown")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.websocket("/ws/health")
async def health_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time health monitoring."""
    connection_id = str(uuid.uuid4())
    await websocket.accept()
    active_connections[connection_id] = websocket
    
    try:
        while True:
            # Send health status every 5 seconds
            try:
                voice_interface = container.get_voice_interface()
                health_status = await voice_interface.get_health_status()
                
                await websocket.send_json({
                    "type": "health_update",
                    "data": health_status
                })
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error sending health update: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection {connection_id} disconnected")
    finally:
        active_connections.pop(connection_id, None)


@app.post("/api/consultation/text")
async def text_consultation(
    symptoms: str = Form(...),
    patient_age: Optional[int] = Form(None),
    patient_gender: Optional[str] = Form(None),
    medical_history: Optional[str] = Form(None)
):
    """Handle text-based medical consultation."""
    try:
        # Create patient if demographics provided
        patient = None
        if patient_age or patient_gender or medical_history:
            patient = Patient.create_anonymous()
            if patient_age:
                patient.age = patient_age
            if patient_gender:
                patient.gender = patient_gender
            if medical_history:
                history_list = medical_history.split(",")
                for condition in history_list:
                    condition = condition.strip()
                    if condition:
                        patient.add_medical_history_item(condition)
        
        # Create symptoms object
        medical_symptoms = MedicalSymptoms.from_text(symptoms)
        
        # Get medical analysis use case
        medical_analysis = container.get_medical_analysis_use_case()
        
        # Perform analysis
        response = await medical_analysis.analyze_patient_symptoms(
            medical_symptoms, patient
        )
        
        return {
            "success": True,
            "consultation_id": str(uuid.uuid4()),
            "analysis": {
                "urgency": response.urgency.value,
                "confidence": response.confidence,
                "is_emergency": response.is_emergency,
                "recommendations": response.recommendations,
                "red_flags": response.red_flags,
                "patient_friendly_response": response.to_patient_friendly_text(),
                "model_used": response.model_used
            }
        }
        
    except Exception as e:
        logger.error(f"Text consultation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/consultation/voice")
async def voice_consultation(
    audio_file: UploadFile = File(...),
    patient_age: Optional[int] = Form(None),
    patient_gender: Optional[str] = Form(None),
    medical_history: Optional[str] = Form(None)
):
    """Handle voice-based medical consultation."""
    try:
        # Read audio file
        audio_content = await audio_file.read()
        
        # Create patient (always create one for voice consultation)
        patient = Patient.create_anonymous()
        if patient_age:
            patient.age = int(patient_age) if str(patient_age).isdigit() else None
        if patient_gender:
            patient.gender = patient_gender
        if medical_history:
            history_list = medical_history.split(",")
            for condition in history_list:
                condition = condition.strip()
                if condition:
                    patient.add_medical_history_item(condition)
        
        # Get voice consultation use case
        voice_consultation = container.get_voice_consultation_use_case()
        
        # Perform voice consultation - need to create a temporary audio file
        import tempfile
        import os

        # Save audio content to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_content)
            temp_audio_path = temp_file.name

        try:
            # Use execute_text_to_voice_consultation for uploaded audio
            # First, we need to transcribe the audio to get symptoms text
            # For now, we'll use a placeholder - in production, you'd transcribe first
            symptoms_text = "Audio symptoms uploaded - requires transcription"

            result = await voice_consultation.execute_text_to_voice_consultation(
                patient, symptoms_text
            )
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
        
        return {
            "success": True,
            "consultation_id": result.id,
            "transcription": result.transcription,
            "analysis": {
                "urgency": result.medical_response.urgency.value,
                "confidence": result.medical_response.confidence,
                "is_emergency": result.medical_response.is_emergency,
                "recommendations": result.medical_response.recommendations,
                "red_flags": result.medical_response.red_flags,
                "patient_friendly_response": result.medical_response.to_patient_friendly_text(),
                "model_used": result.medical_response.model_used
            },
            "has_audio_response": result.audio_response is not None,
            "processing_time_ms": (result.completed_at - result.created_at).total_seconds() * 1000 if result.completed_at else 0
        }
        
    except Exception as e:
        logger.error(f"Voice consultation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resilience/status")
async def resilience_status():
    """Get current resilience patterns status."""
    try:
        voice_interface = container.get_voice_interface()
        
        # Get circuit breaker states
        asr_cb = voice_interface.asr_circuit_breaker
        tts_cb = voice_interface.tts_circuit_breaker
        
        # Get retry policy stats
        asr_retry = voice_interface.asr_retry_policy
        
        # Get stats (circuit breaker is async, retry policy is sync)
        asr_stats = await asr_cb.get_stats()
        tts_stats = await tts_cb.get_stats()
        asr_retry_stats = asr_retry.get_stats()

        return {
            "circuit_breakers": {
                "asr": asr_stats,
                "tts": tts_stats
            },
            "retry_policies": {
                "asr": asr_retry_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get resilience status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced Medical Diagnosis Endpoints

@app.post("/api/consultation/enhanced")
async def enhanced_consultation(
    symptoms: str = Form(...),
    patient_age: Optional[int] = Form(None),
    patient_gender: Optional[str] = Form(None),
    medical_history: Optional[str] = Form(None)
):
    """Enhanced medical consultation with interactive diagnosis and drug recommendations."""
    try:
        if not enhanced_medical_adapter:
            raise HTTPException(status_code=503, detail="Enhanced medical service not available")

        # Create patient
        patient = None
        if patient_age or patient_gender or medical_history:
            patient = Patient.create_anonymous()
            if patient_age:
                patient.age = patient_age
            if patient_gender:
                patient.gender = patient_gender
            if medical_history:
                history_list = medical_history.split(",")
                for condition in history_list:
                    condition = condition.strip()
                    if condition:
                        patient.add_medical_history_item(condition)

        # Create symptoms object
        medical_symptoms = MedicalSymptoms.from_text(symptoms)

        # Start progress tracking
        session_id = str(uuid.uuid4())
        await progress_tracking_service.start_progress_tracking(session_id, "enhanced_diagnosis")

        # Perform enhanced analysis
        await progress_tracking_service.update_progress(session_id, ProgressStage.ANALYZING_SYMPTOMS)
        response = await enhanced_medical_adapter.analyze_symptoms(medical_symptoms, patient)

        await progress_tracking_service.update_progress(session_id, ProgressStage.FINDING_MEDICATIONS)

        # Get drug recommendations
        drug_recommendations = []
        if drug_recommendation_service and response.recommendations:
            primary_diagnosis = response.recommendations[0] if response.recommendations else "general symptoms"
            drug_recommendations = await drug_recommendation_service.get_drug_recommendations(
                primary_diagnosis, medical_symptoms, patient
            )

        await progress_tracking_service.complete_progress(session_id, "Enhanced analysis complete")

        return {
            "success": True,
            "consultation_id": session_id,
            "analysis": {
                "urgency": response.urgency.value,
                "confidence": response.confidence,
                "is_emergency": response.is_emergency,
                "recommendations": response.recommendations,
                "red_flags": response.red_flags,
                "patient_friendly_response": response.to_patient_friendly_text(),
                "model_used": response.model_used,
                "follow_up_questions": response.metadata.get("follow_up_questions", []),
                "drug_recommendations": drug_recommendations,
                "processing_time_ms": response.processing_time_ms
            }
        }

    except Exception as e:
        logger.error(f"Enhanced consultation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/diagnosis/interactive/start")
async def start_interactive_diagnosis(
    symptoms: str = Form(...),
    patient_age: Optional[int] = Form(None),
    patient_gender: Optional[str] = Form(None),
    medical_history: Optional[str] = Form(None)
):
    """Start an interactive diagnosis session."""
    try:
        if not interactive_diagnosis_service:
            raise HTTPException(status_code=503, detail="Interactive diagnosis service not available")

        # Create patient
        patient = None
        if patient_age or patient_gender or medical_history:
            patient = Patient.create_anonymous()
            if patient_age:
                patient.age = patient_age
            if patient_gender:
                patient.gender = patient_gender
            if medical_history:
                history_list = medical_history.split(",")
                for condition in history_list:
                    condition = condition.strip()
                    if condition:
                        patient.add_medical_history_item(condition)

        # Create symptoms object
        medical_symptoms = MedicalSymptoms.from_text(symptoms)

        # Start interactive session
        session_result = await interactive_diagnosis_service.start_interactive_session(
            medical_symptoms, patient
        )

        return {
            "success": True,
            **session_result
        }

    except Exception as e:
        logger.error(f"Failed to start interactive diagnosis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/diagnosis/interactive/answer")
async def answer_interactive_question(
    session_id: str = Form(...),
    question_id: str = Form(...),
    answer: str = Form(...)
):
    """Answer a question in an interactive diagnosis session."""
    try:
        if not interactive_diagnosis_service:
            raise HTTPException(status_code=503, detail="Interactive diagnosis service not available")

        result = await interactive_diagnosis_service.answer_question(
            session_id, question_id, answer
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        logger.error(f"Failed to answer interactive question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Set environment variables for demo
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("USE_MOCK_ADAPTERS", "false")
    os.environ.setdefault("MEDICAL_MODEL", "google/flan-t5-base")
    os.environ.setdefault("MEDICAL_DEVICE", "auto")
    os.environ.setdefault("FORCE_TORCH_DTYPE", "float32")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
