// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  WS_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/health',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
} as const;

// API Endpoints
export const API_ENDPOINTS = {
  CONSULTATION: {
    TEXT: '/api/consultation/text',
    VOICE: '/api/consultation/voice',
    ENHANCED: '/api/consultation/enhanced',
  },
  DIAGNOSIS: {
    INTERACTIVE_START: '/api/diagnosis/interactive/start',
    INTERACTIVE_ANSWER: '/api/diagnosis/interactive/answer',
    INTERACTIVE_STATUS: '/api/diagnosis/interactive/status',
  },
  HEALTH: {
    STATUS: '/api/health',
    RESILIENCE: '/api/resilience/status',
  },
  WEBSOCKET: {
    HEALTH: '/ws/health',
    PROGRESS: '/ws/progress',
  },
} as const;

// Form Validation
export const VALIDATION_RULES = {
  SYMPTOMS: {
    MIN_LENGTH: 10,
    MAX_LENGTH: 2000,
  },
  PATIENT_AGE: {
    MIN: 0,
    MAX: 150,
  },
  MEDICAL_HISTORY: {
    MAX_LENGTH: 1000,
  },
  AUDIO: {
    MAX_DURATION: 300000, // 5 minutes in milliseconds
    MAX_SIZE: 50 * 1024 * 1024, // 50MB
    SUPPORTED_FORMATS: ['audio/webm', 'audio/mp4', 'audio/mpeg', 'audio/wav'],
  },
} as const;

// UI Constants
export const UI_CONSTANTS = {
  DEBOUNCE_DELAY: 300,
  TOAST_DURATION: 5000,
  LOADING_DELAY: 200, // Delay before showing loading spinner
  ANIMATION_DURATION: 200,
} as const;

// WebSocket Configuration
export const WEBSOCKET_CONFIG = {
  RECONNECT_ATTEMPTS: 5,
  RECONNECT_DELAY: 1000,
  HEARTBEAT_INTERVAL: 30000, // 30 seconds
  CONNECTION_TIMEOUT: 10000, // 10 seconds
} as const;

// Audio Recording Configuration
export const AUDIO_CONFIG = {
  DEFAULT_MIME_TYPE: 'audio/webm;codecs=opus',
  FALLBACK_MIME_TYPE: 'audio/webm',
  BITS_PER_SECOND: 128000,
  MAX_DURATION: 300000, // 5 minutes
  CHUNK_INTERVAL: 1000, // 1 second
} as const;

// Progress Stages
export const PROGRESS_STAGES = {
  INITIALIZING: 'initializing',
  ANALYZING_SYMPTOMS: 'analyzing_symptoms',
  GENERATING_QUESTIONS: 'generating_questions',
  PROCESSING_RESPONSES: 'processing_responses',
  GENERATING_DIAGNOSIS: 'generating_diagnosis',
  RECOMMENDING_TREATMENTS: 'recommending_treatments',
  FINALIZING_RESULTS: 'finalizing_results',
  COMPLETED: 'completed',
  ERROR: 'error',
} as const;

// Urgency Levels
export const URGENCY_LEVELS = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL',
} as const;

// Gender Options
export const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
] as const;

// Error Codes
export const ERROR_CODES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  PERMISSION_ERROR: 'PERMISSION_ERROR',
  AUDIO_ERROR: 'AUDIO_ERROR',
  WEBSOCKET_ERROR: 'WEBSOCKET_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  USER_PREFERENCES: 'medvaani_user_preferences',
  CONSULTATION_HISTORY: 'medvaani_consultation_history',
  AUDIO_SETTINGS: 'medvaani_audio_settings',
  THEME_PREFERENCE: 'medvaani_theme',
} as const;

// Theme Configuration
export const THEME = {
  COLORS: {
    PRIMARY: '#2563eb',
    PRIMARY_DARK: '#1d4ed8',
    SUCCESS: '#059669',
    SUCCESS_DARK: '#047857',
    WARNING: '#ea580c',
    DANGER: '#dc2626',
    GRAY_50: '#f9fafb',
    GRAY_100: '#f3f4f6',
    GRAY_200: '#e5e7eb',
    GRAY_300: '#d1d5db',
    GRAY_600: '#4b5563',
    GRAY_700: '#374151',
    GRAY_900: '#111827',
  },
  BREAKPOINTS: {
    SM: '640px',
    MD: '768px',
    LG: '1024px',
    XL: '1280px',
  },
} as const;

// Feature Flags
export const FEATURE_FLAGS = {
  ENABLE_VOICE_RECORDING: true,
  ENABLE_ENHANCED_CONSULTATION: true,
  ENABLE_INTERACTIVE_DIAGNOSIS: true,
  ENABLE_HEALTH_MONITORING: true,
  ENABLE_PROGRESS_TRACKING: true,
  ENABLE_OFFLINE_MODE: false,
  ENABLE_ANALYTICS: false,
} as const;

// Default Values
export const DEFAULTS = {
  CONSULTATION_TYPE: 'text',
  LANGUAGE: 'en',
  THEME: 'light',
  AUDIO_QUALITY: 'standard',
} as const;
