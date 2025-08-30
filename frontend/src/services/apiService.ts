import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { 
  ApiResponse, 
  ConsultationRequest, 
  VoiceConsultationRequest,
  ConsultationResponse,
  EnhancedConsultationResponse,
  HealthStatus,
  ApiError 
} from '@/types/api';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 seconds timeout
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`[API] Response ${response.status} from ${response.config.url}`);
        return response;
      },
      (error: AxiosError) => {
        console.error('[API] Response error:', error);
        return Promise.reject(this.handleApiError(error));
      }
    );
  }

  private handleApiError(error: AxiosError): ApiError {
    const apiError: ApiError = {
      code: 'UNKNOWN_ERROR',
      message: 'An unexpected error occurred',
      timestamp: new Date().toISOString(),
    };

    if (error.response) {
      // Server responded with error status
      apiError.code = `HTTP_${error.response.status}`;
      apiError.message = error.response.data?.message || error.message;
      apiError.details = error.response.data;
    } else if (error.request) {
      // Request was made but no response received
      apiError.code = 'NETWORK_ERROR';
      apiError.message = 'Network error - please check your connection';
    } else {
      // Something else happened
      apiError.message = error.message;
    }

    return apiError;
  }

  // Text consultation
  async submitTextConsultation(data: ConsultationRequest): Promise<ConsultationResponse> {
    const formData = new FormData();
    formData.append('symptoms', data.symptoms);
    
    if (data.patient_age) formData.append('patient_age', data.patient_age.toString());
    if (data.patient_gender) formData.append('patient_gender', data.patient_gender);
    if (data.medical_history) formData.append('medical_history', data.medical_history);

    const response = await this.api.post<ConsultationResponse>('/api/consultation/text', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    return response.data;
  }

  // Voice consultation
  async submitVoiceConsultation(data: VoiceConsultationRequest): Promise<ConsultationResponse> {
    const formData = new FormData();
    formData.append('audio_file', data.audio_file);
    formData.append('symptoms', data.symptoms);
    
    if (data.patient_age) formData.append('patient_age', data.patient_age.toString());
    if (data.patient_gender) formData.append('patient_gender', data.patient_gender);
    if (data.medical_history) formData.append('medical_history', data.medical_history);

    const response = await this.api.post<ConsultationResponse>('/api/consultation/voice', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    return response.data;
  }

  // Enhanced consultation
  async submitEnhancedConsultation(data: ConsultationRequest): Promise<EnhancedConsultationResponse> {
    const formData = new FormData();
    formData.append('symptoms', data.symptoms);
    
    if (data.patient_age) formData.append('patient_age', data.patient_age.toString());
    if (data.patient_gender) formData.append('patient_gender', data.patient_gender);
    if (data.medical_history) formData.append('medical_history', data.medical_history);

    const response = await this.api.post<EnhancedConsultationResponse>('/api/consultation/enhanced', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    return response.data;
  }

  // Start interactive diagnosis
  async startInteractiveDiagnosis(data: ConsultationRequest): Promise<any> {
    const formData = new FormData();
    formData.append('symptoms', data.symptoms);
    
    if (data.patient_age) formData.append('patient_age', data.patient_age.toString());
    if (data.patient_gender) formData.append('patient_gender', data.patient_gender);
    if (data.medical_history) formData.append('medical_history', data.medical_history);

    const response = await this.api.post('/api/diagnosis/interactive/start', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    return response.data;
  }

  // Get health status
  async getHealthStatus(): Promise<HealthStatus> {
    const response = await this.api.get<HealthStatus>('/api/health');
    return response.data;
  }

  // Get resilience status
  async getResilienceStatus(): Promise<any> {
    const response = await this.api.get('/api/resilience/status');
    return response.data;
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
