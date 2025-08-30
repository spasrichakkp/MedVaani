// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Consultation Types
export interface ConsultationRequest {
  symptoms: string;
  patient_age?: number;
  patient_gender?: string;
  medical_history?: string;
}

export interface VoiceConsultationRequest extends ConsultationRequest {
  audio_file: File;
}

export interface ConsultationResponse {
  consultation_id: string;
  analysis: {
    urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    confidence: number;
    is_emergency: boolean;
    recommendations: string[];
    red_flags: string[];
    patient_friendly_response: string;
    model_used: string;
  };
}

// Enhanced Consultation Types
export interface EnhancedConsultationResponse extends ConsultationResponse {
  interactive_session?: {
    session_id: string;
    questions: InteractiveQuestion[];
    current_step: number;
    total_steps: number;
  };
  drug_recommendations?: DrugRecommendation[];
}

export interface InteractiveQuestion {
  id: string;
  question: string;
  type: 'multiple_choice' | 'yes_no' | 'text' | 'scale';
  options?: string[];
  required: boolean;
}

export interface DrugRecommendation {
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
  warnings: string[];
  interactions: string[];
}

// Health Monitoring Types
export interface HealthStatus {
  status: 'healthy' | 'warning' | 'error';
  services: {
    [serviceName: string]: {
      status: 'up' | 'down' | 'degraded';
      response_time?: number;
      last_check: string;
      error_message?: string;
    };
  };
  system_metrics: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

// Progress Tracking Types
export interface ProgressUpdate {
  consultation_id: string;
  stage: 'initializing' | 'analyzing_symptoms' | 'generating_questions' | 
         'processing_responses' | 'generating_diagnosis' | 'recommending_treatments' | 
         'finalizing_results' | 'completed' | 'error';
  progress_percentage: number;
  current_step: string;
  estimated_time_remaining?: number;
  error_message?: string;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'health_update' | 'progress_update' | 'error' | 'connection_status';
  data: HealthStatus | ProgressUpdate | { message: string };
  timestamp: string;
}

// Error Types
export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}
