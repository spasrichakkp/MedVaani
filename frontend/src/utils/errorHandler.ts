import { ApiError } from '@/types/api';

export interface ErrorHandlerOptions {
  showToast?: boolean;
  logToConsole?: boolean;
  reportToService?: boolean;
}

class ErrorHandler {
  private defaultOptions: ErrorHandlerOptions = {
    showToast: true,
    logToConsole: true,
    reportToService: false,
  };

  handle(error: any, options: ErrorHandlerOptions = {}): ApiError {
    const opts = { ...this.defaultOptions, ...options };
    
    // Normalize error to ApiError format
    const apiError = this.normalizeError(error);
    
    // Log to console if enabled
    if (opts.logToConsole) {
      console.error('[ErrorHandler]', apiError);
    }
    
    // Show toast notification if enabled
    if (opts.showToast) {
      this.showErrorToast(apiError);
    }
    
    // Report to error tracking service if enabled
    if (opts.reportToService) {
      this.reportError(apiError);
    }
    
    return apiError;
  }

  private normalizeError(error: any): ApiError {
    // If it's already an ApiError, return as is
    if (error && typeof error === 'object' && error.code && error.message) {
      return error as ApiError;
    }

    // Handle different error types
    if (error instanceof Error) {
      return {
        code: error.name || 'ERROR',
        message: error.message,
        timestamp: new Date().toISOString(),
      };
    }

    // Handle string errors
    if (typeof error === 'string') {
      return {
        code: 'STRING_ERROR',
        message: error,
        timestamp: new Date().toISOString(),
      };
    }

    // Handle network errors
    if (error?.code === 'NETWORK_ERROR') {
      return {
        code: 'NETWORK_ERROR',
        message: 'Network connection failed. Please check your internet connection.',
        timestamp: new Date().toISOString(),
      };
    }

    // Default fallback
    return {
      code: 'UNKNOWN_ERROR',
      message: 'An unexpected error occurred',
      details: error,
      timestamp: new Date().toISOString(),
    };
  }

  private showErrorToast(error: ApiError): void {
    // For now, we'll use console.error
    // In a real app, you'd integrate with a toast library like react-hot-toast
    console.error('🚨 Error:', error.message);
    
    // You could also create a custom toast system or integrate with libraries like:
    // - react-hot-toast
    // - react-toastify
    // - chakra-ui toast
    // - antd notification
  }

  private reportError(error: ApiError): void {
    // In a production app, you'd send this to an error tracking service like:
    // - Sentry
    // - Bugsnag
    // - LogRocket
    // - Custom logging endpoint
    
    console.log('[ErrorHandler] Would report to error service:', error);
  }

  // Specific error handlers for common scenarios
  handleNetworkError(): ApiError {
    return this.handle({
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server. Please check your internet connection and try again.',
    });
  }

  handleValidationError(field: string, message: string): ApiError {
    return this.handle({
      code: 'VALIDATION_ERROR',
      message: `${field}: ${message}`,
    });
  }

  handlePermissionError(permission: string): ApiError {
    return this.handle({
      code: 'PERMISSION_ERROR',
      message: `Permission denied: ${permission}. Please grant the required permissions and try again.`,
    });
  }

  handleTimeoutError(): ApiError {
    return this.handle({
      code: 'TIMEOUT_ERROR',
      message: 'Request timed out. Please try again.',
    });
  }

  handleServerError(statusCode: number): ApiError {
    const message = this.getServerErrorMessage(statusCode);
    return this.handle({
      code: `HTTP_${statusCode}`,
      message,
    });
  }

  private getServerErrorMessage(statusCode: number): string {
    switch (statusCode) {
      case 400:
        return 'Bad request. Please check your input and try again.';
      case 401:
        return 'Authentication required. Please log in and try again.';
      case 403:
        return 'Access forbidden. You do not have permission to perform this action.';
      case 404:
        return 'Resource not found. The requested item may have been moved or deleted.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Internal server error. Please try again later.';
      case 502:
        return 'Bad gateway. The server is temporarily unavailable.';
      case 503:
        return 'Service unavailable. Please try again later.';
      case 504:
        return 'Gateway timeout. The server took too long to respond.';
      default:
        return `Server error (${statusCode}). Please try again later.`;
    }
  }

  // Utility method to check if an error is retryable
  isRetryableError(error: ApiError): boolean {
    const retryableCodes = [
      'NETWORK_ERROR',
      'TIMEOUT_ERROR',
      'HTTP_429',
      'HTTP_500',
      'HTTP_502',
      'HTTP_503',
      'HTTP_504',
    ];
    
    return retryableCodes.includes(error.code);
  }

  // Utility method to get user-friendly error message
  getUserFriendlyMessage(error: ApiError): string {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return 'Connection problem. Please check your internet and try again.';
      case 'PERMISSION_ERROR':
        return 'Permission required. Please allow access and try again.';
      case 'VALIDATION_ERROR':
        return 'Please check your input and try again.';
      case 'TIMEOUT_ERROR':
        return 'Request took too long. Please try again.';
      default:
        return error.message || 'Something went wrong. Please try again.';
    }
  }
}

// Export singleton instance
export const errorHandler = new ErrorHandler();
export default errorHandler;
