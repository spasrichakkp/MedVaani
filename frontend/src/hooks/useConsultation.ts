import { useState, useCallback } from 'react';
import { apiService } from '@/services/apiService';
import { errorHandler } from '@/utils/errorHandler';
import { 
  ConsultationRequest, 
  VoiceConsultationRequest,
  ConsultationResponse,
  EnhancedConsultationResponse,
  ApiError 
} from '@/types/api';

export interface UseConsultationOptions {
  onSuccess?: (result: ConsultationResponse | EnhancedConsultationResponse) => void;
  onError?: (error: ApiError) => void;
  autoRetry?: boolean;
  maxRetries?: number;
}

export interface UseConsultationReturn {
  isLoading: boolean;
  result: ConsultationResponse | EnhancedConsultationResponse | null;
  error: ApiError | null;
  submitTextConsultation: (data: ConsultationRequest) => Promise<ConsultationResponse | null>;
  submitVoiceConsultation: (data: VoiceConsultationRequest) => Promise<ConsultationResponse | null>;
  submitEnhancedConsultation: (data: ConsultationRequest) => Promise<EnhancedConsultationResponse | null>;
  startInteractiveDiagnosis: (data: ConsultationRequest) => Promise<any>;
  clearResult: () => void;
  clearError: () => void;
  retry: () => Promise<void>;
}

export function useConsultation(options: UseConsultationOptions = {}): UseConsultationReturn {
  const { onSuccess, onError, autoRetry = false, maxRetries = 3 } = options;

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ConsultationResponse | EnhancedConsultationResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [lastRequest, setLastRequest] = useState<{
    type: 'text' | 'voice' | 'enhanced' | 'interactive';
    data: ConsultationRequest | VoiceConsultationRequest;
  } | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const handleSuccess = useCallback((response: ConsultationResponse | EnhancedConsultationResponse) => {
    setResult(response);
    setError(null);
    setRetryCount(0);
    
    if (onSuccess) {
      onSuccess(response);
    }
  }, [onSuccess]);

  const handleError = useCallback((err: any) => {
    const apiError = errorHandler.handle(err);
    setError(apiError);
    setResult(null);
    
    if (onError) {
      onError(apiError);
    }

    // Auto-retry for retryable errors
    if (autoRetry && retryCount < maxRetries && errorHandler.isRetryableError(apiError)) {
      setTimeout(() => {
        retry();
      }, Math.pow(2, retryCount) * 1000); // Exponential backoff
    }
  }, [onError, autoRetry, maxRetries, retryCount]);

  const submitTextConsultation = useCallback(async (data: ConsultationRequest): Promise<ConsultationResponse | null> => {
    setIsLoading(true);
    setError(null);
    setLastRequest({ type: 'text', data });

    try {
      const response = await apiService.submitTextConsultation(data);
      handleSuccess(response);
      return response;
    } catch (err) {
      handleError(err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [handleSuccess, handleError]);

  const submitVoiceConsultation = useCallback(async (data: VoiceConsultationRequest): Promise<ConsultationResponse | null> => {
    setIsLoading(true);
    setError(null);
    setLastRequest({ type: 'voice', data });

    try {
      const response = await apiService.submitVoiceConsultation(data);
      handleSuccess(response);
      return response;
    } catch (err) {
      handleError(err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [handleSuccess, handleError]);

  const submitEnhancedConsultation = useCallback(async (data: ConsultationRequest): Promise<EnhancedConsultationResponse | null> => {
    setIsLoading(true);
    setError(null);
    setLastRequest({ type: 'enhanced', data });

    try {
      const response = await apiService.submitEnhancedConsultation(data);
      handleSuccess(response);
      return response;
    } catch (err) {
      handleError(err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [handleSuccess, handleError]);

  const startInteractiveDiagnosis = useCallback(async (data: ConsultationRequest): Promise<any> => {
    setIsLoading(true);
    setError(null);
    setLastRequest({ type: 'interactive', data });

    try {
      const response = await apiService.startInteractiveDiagnosis(data);
      handleSuccess(response);
      return response;
    } catch (err) {
      handleError(err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [handleSuccess, handleError]);

  const retry = useCallback(async (): Promise<void> => {
    if (!lastRequest || retryCount >= maxRetries) {
      return;
    }

    setRetryCount(prev => prev + 1);

    switch (lastRequest.type) {
      case 'text':
        await submitTextConsultation(lastRequest.data as ConsultationRequest);
        break;
      case 'voice':
        await submitVoiceConsultation(lastRequest.data as VoiceConsultationRequest);
        break;
      case 'enhanced':
        await submitEnhancedConsultation(lastRequest.data as ConsultationRequest);
        break;
      case 'interactive':
        await startInteractiveDiagnosis(lastRequest.data as ConsultationRequest);
        break;
    }
  }, [lastRequest, retryCount, maxRetries, submitTextConsultation, submitVoiceConsultation, submitEnhancedConsultation, startInteractiveDiagnosis]);

  const clearResult = useCallback((): void => {
    setResult(null);
  }, []);

  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  return {
    isLoading,
    result,
    error,
    submitTextConsultation,
    submitVoiceConsultation,
    submitEnhancedConsultation,
    startInteractiveDiagnosis,
    clearResult,
    clearError,
    retry,
  };
}

// Specialized hook for text consultations only
export function useTextConsultation(options: UseConsultationOptions = {}) {
  const consultation = useConsultation(options);
  
  return {
    isLoading: consultation.isLoading,
    result: consultation.result,
    error: consultation.error,
    submit: consultation.submitTextConsultation,
    clearResult: consultation.clearResult,
    clearError: consultation.clearError,
    retry: consultation.retry,
  };
}

// Specialized hook for voice consultations only
export function useVoiceConsultation(options: UseConsultationOptions = {}) {
  const consultation = useConsultation(options);
  
  return {
    isLoading: consultation.isLoading,
    result: consultation.result,
    error: consultation.error,
    submit: consultation.submitVoiceConsultation,
    clearResult: consultation.clearResult,
    clearError: consultation.clearError,
    retry: consultation.retry,
  };
}

// Specialized hook for enhanced consultations only
export function useEnhancedConsultation(options: UseConsultationOptions = {}) {
  const consultation = useConsultation(options);
  
  return {
    isLoading: consultation.isLoading,
    result: consultation.result as EnhancedConsultationResponse | null,
    error: consultation.error,
    submit: consultation.submitEnhancedConsultation,
    clearResult: consultation.clearResult,
    clearError: consultation.clearError,
    retry: consultation.retry,
  };
}
