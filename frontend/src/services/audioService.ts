export interface AudioRecordingOptions {
  mimeType?: string;
  audioBitsPerSecond?: number;
  maxDuration?: number; // in milliseconds
}

export interface AudioRecordingResult {
  blob: Blob;
  duration: number;
  size: number;
  mimeType: string;
}

class AudioService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private startTime: number = 0;
  private isRecording = false;

  // Default recording options
  private defaultOptions: AudioRecordingOptions = {
    mimeType: 'audio/webm;codecs=opus',
    audioBitsPerSecond: 128000,
    maxDuration: 300000, // 5 minutes max
  };

  async checkMicrophonePermission(): Promise<boolean> {
    try {
      const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
      return permission.state === 'granted';
    } catch (error) {
      console.warn('[AudioService] Permission API not supported, trying direct access');
      return this.requestMicrophoneAccess();
    }
  }

  async requestMicrophoneAccess(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop()); // Stop immediately, just testing access
      return true;
    } catch (error) {
      console.error('[AudioService] Microphone access denied:', error);
      return false;
    }
  }

  async startRecording(options: AudioRecordingOptions = {}): Promise<void> {
    if (this.isRecording) {
      throw new Error('Recording already in progress');
    }

    const recordingOptions = { ...this.defaultOptions, ...options };

    try {
      // Request microphone access
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      // Check if the browser supports the requested MIME type
      let mimeType = recordingOptions.mimeType!;
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        console.warn(`[AudioService] ${mimeType} not supported, falling back to default`);
        mimeType = 'audio/webm'; // Fallback
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = ''; // Let browser choose
        }
      }

      // Create MediaRecorder
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: mimeType || undefined,
        audioBitsPerSecond: recordingOptions.audioBitsPerSecond,
      });

      // Reset audio chunks
      this.audioChunks = [];

      // Set up event handlers
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onerror = (event) => {
        console.error('[AudioService] MediaRecorder error:', event);
        this.cleanup();
        throw new Error('Recording failed');
      };

      // Start recording
      this.mediaRecorder.start(1000); // Collect data every second
      this.startTime = Date.now();
      this.isRecording = true;

      // Set maximum duration timeout
      if (recordingOptions.maxDuration) {
        setTimeout(() => {
          if (this.isRecording) {
            console.warn('[AudioService] Maximum recording duration reached, stopping');
            this.stopRecording();
          }
        }, recordingOptions.maxDuration);
      }

      console.log('[AudioService] Recording started');

    } catch (error) {
      this.cleanup();
      throw new Error(`Failed to start recording: ${error}`);
    }
  }

  async stopRecording(): Promise<AudioRecordingResult> {
    if (!this.isRecording || !this.mediaRecorder) {
      throw new Error('No recording in progress');
    }

    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('MediaRecorder not available'));
        return;
      }

      this.mediaRecorder.onstop = () => {
        try {
          const duration = Date.now() - this.startTime;
          const mimeType = this.mediaRecorder?.mimeType || 'audio/webm';
          
          // Create blob from chunks
          const blob = new Blob(this.audioChunks, { type: mimeType });
          
          const result: AudioRecordingResult = {
            blob,
            duration,
            size: blob.size,
            mimeType,
          };

          console.log('[AudioService] Recording stopped:', {
            duration: `${duration}ms`,
            size: `${blob.size} bytes`,
            mimeType,
          });

          this.cleanup();
          resolve(result);

        } catch (error) {
          this.cleanup();
          reject(error);
        }
      };

      this.mediaRecorder.stop();
      this.isRecording = false;
    });
  }

  cancelRecording(): void {
    if (this.isRecording && this.mediaRecorder) {
      this.mediaRecorder.stop();
      this.isRecording = false;
    }
    this.cleanup();
    console.log('[AudioService] Recording cancelled');
  }

  private cleanup(): void {
    // Stop all tracks
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    // Clear MediaRecorder
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.startTime = 0;
  }

  getRecordingState(): 'inactive' | 'recording' | 'paused' {
    if (!this.mediaRecorder) return 'inactive';
    return this.mediaRecorder.state;
  }

  isCurrentlyRecording(): boolean {
    return this.isRecording;
  }

  // Utility method to convert blob to File for API upload
  blobToFile(blob: Blob, filename: string = 'recording.webm'): File {
    return new File([blob], filename, { type: blob.type });
  }

  // Get supported MIME types
  getSupportedMimeTypes(): string[] {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/mpeg',
      'audio/wav',
    ];

    return types.filter(type => MediaRecorder.isTypeSupported(type));
  }
}

// Export singleton instance
export const audioService = new AudioService();
export default audioService;
