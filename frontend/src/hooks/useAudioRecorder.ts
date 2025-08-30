import { useState, useCallback, useRef, useEffect } from 'react';
import { audioService, AudioRecordingOptions, AudioRecordingResult } from '@/services/audioService';
import { errorHandler } from '@/utils/errorHandler';

export interface UseAudioRecorderOptions extends AudioRecordingOptions {
  onRecordingStart?: () => void;
  onRecordingStop?: (result: AudioRecordingResult) => void;
  onRecordingError?: (error: string) => void;
  onPermissionDenied?: () => void;
}

export interface UseAudioRecorderReturn {
  isRecording: boolean;
  isPaused: boolean;
  recordingDuration: number;
  hasPermission: boolean | null;
  error: string | null;
  recordingResult: AudioRecordingResult | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<AudioRecordingResult | null>;
  cancelRecording: () => void;
  requestPermission: () => Promise<boolean>;
  clearError: () => void;
  clearResult: () => void;
}

export function useAudioRecorder(options: UseAudioRecorderOptions = {}): UseAudioRecorderReturn {
  const {
    onRecordingStart,
    onRecordingStop,
    onRecordingError,
    onPermissionDenied,
    ...recordingOptions
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recordingResult, setRecordingResult] = useState<AudioRecordingResult | null>(null);

  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  // Check permission on mount
  useEffect(() => {
    checkPermission();
  }, []);

  // Update recording duration
  useEffect(() => {
    if (isRecording && !isPaused) {
      startTimeRef.current = Date.now() - recordingDuration;
      durationIntervalRef.current = setInterval(() => {
        setRecordingDuration(Date.now() - startTimeRef.current);
      }, 100);
    } else {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
    }

    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [isRecording, isPaused, recordingDuration]);

  const checkPermission = useCallback(async (): Promise<boolean> => {
    try {
      const permission = await audioService.checkMicrophonePermission();
      setHasPermission(permission);
      return permission;
    } catch (err) {
      console.error('[useAudioRecorder] Permission check failed:', err);
      setHasPermission(false);
      return false;
    }
  }, []);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      setError(null);
      const permission = await audioService.requestMicrophoneAccess();
      setHasPermission(permission);
      
      if (!permission && onPermissionDenied) {
        onPermissionDenied();
      }
      
      return permission;
    } catch (err) {
      const errorMessage = 'Microphone permission denied. Please allow access and try again.';
      setError(errorMessage);
      setHasPermission(false);
      
      if (onRecordingError) {
        onRecordingError(errorMessage);
      }
      
      return false;
    }
  }, [onPermissionDenied, onRecordingError]);

  const startRecording = useCallback(async (): Promise<void> => {
    try {
      setError(null);
      setRecordingResult(null);

      // Check permission first
      if (hasPermission === null) {
        await checkPermission();
      }

      if (hasPermission === false) {
        const granted = await requestPermission();
        if (!granted) {
          throw new Error('Microphone permission required');
        }
      }

      // Start recording
      await audioService.startRecording(recordingOptions);
      
      setIsRecording(true);
      setIsPaused(false);
      setRecordingDuration(0);
      startTimeRef.current = Date.now();

      if (onRecordingStart) {
        onRecordingStart();
      }

    } catch (err) {
      const error = errorHandler.handle(err);
      setError(error.message);
      setIsRecording(false);
      
      if (onRecordingError) {
        onRecordingError(error.message);
      }
      
      throw err;
    }
  }, [hasPermission, recordingOptions, onRecordingStart, onRecordingError, checkPermission, requestPermission]);

  const stopRecording = useCallback(async (): Promise<AudioRecordingResult | null> => {
    if (!isRecording) {
      return null;
    }

    try {
      const result = await audioService.stopRecording();
      
      setIsRecording(false);
      setIsPaused(false);
      setRecordingResult(result);

      if (onRecordingStop) {
        onRecordingStop(result);
      }

      return result;

    } catch (err) {
      const error = errorHandler.handle(err);
      setError(error.message);
      setIsRecording(false);
      setIsPaused(false);
      
      if (onRecordingError) {
        onRecordingError(error.message);
      }
      
      return null;
    }
  }, [isRecording, onRecordingStop, onRecordingError]);

  const cancelRecording = useCallback((): void => {
    if (isRecording) {
      audioService.cancelRecording();
      setIsRecording(false);
      setIsPaused(false);
      setRecordingDuration(0);
      setRecordingResult(null);
    }
  }, [isRecording]);

  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  const clearResult = useCallback((): void => {
    setRecordingResult(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isRecording) {
        audioService.cancelRecording();
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [isRecording]);

  return {
    isRecording,
    isPaused,
    recordingDuration,
    hasPermission,
    error,
    recordingResult,
    startRecording,
    stopRecording,
    cancelRecording,
    requestPermission,
    clearError,
    clearResult,
  };
}

// Utility hook for formatting recording duration
export function useRecordingDuration(duration: number): string {
  const minutes = Math.floor(duration / 60000);
  const seconds = Math.floor((duration % 60000) / 1000);
  const milliseconds = Math.floor((duration % 1000) / 10);

  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(2, '0')}`;
}
