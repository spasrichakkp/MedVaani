import React from 'react';

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'blue' | 'green' | 'red' | 'gray' | 'white';
  text?: string;
  className?: string;
  fullScreen?: boolean;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

const colorClasses = {
  blue: 'text-blue-600',
  green: 'text-green-600',
  red: 'text-red-600',
  gray: 'text-gray-600',
  white: 'text-white',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'blue',
  text,
  className = '',
  fullScreen = false,
}) => {
  const spinnerElement = (
    <div className={`flex items-center justify-center ${className}`}>
      <div className="flex flex-col items-center space-y-2">
        <svg
          className={`animate-spin ${sizeClasses[size]} ${colorClasses[color]}`}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        {text && (
          <p className={`text-sm ${colorClasses[color]} animate-pulse`}>
            {text}
          </p>
        )}
      </div>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        {spinnerElement}
      </div>
    );
  }

  return spinnerElement;
};

// Specialized loading components for different use cases
export const ButtonSpinner: React.FC<{ size?: 'sm' | 'md' }> = ({ size = 'sm' }) => (
  <LoadingSpinner size={size} color="white" className="mr-2" />
);

export const PageSpinner: React.FC<{ text?: string }> = ({ text = 'Loading...' }) => (
  <LoadingSpinner size="lg" text={text} fullScreen />
);

export const InlineSpinner: React.FC<{ text?: string }> = ({ text }) => (
  <LoadingSpinner size="sm" text={text} className="py-4" />
);

// Loading skeleton components
export const SkeletonLine: React.FC<{ width?: string; className?: string }> = ({ 
  width = 'w-full', 
  className = '' 
}) => (
  <div className={`h-4 bg-gray-200 rounded animate-pulse ${width} ${className}`} />
);

export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
    <div className="animate-pulse">
      <div className="flex items-center space-x-4 mb-4">
        <div className="w-12 h-12 bg-gray-200 rounded-full" />
        <div className="flex-1 space-y-2">
          <SkeletonLine width="w-3/4" />
          <SkeletonLine width="w-1/2" />
        </div>
      </div>
      <div className="space-y-3">
        <SkeletonLine />
        <SkeletonLine />
        <SkeletonLine width="w-5/6" />
      </div>
    </div>
  </div>
);

export const SkeletonForm: React.FC<{ fields?: number }> = ({ fields = 3 }) => (
  <div className="space-y-6">
    {Array.from({ length: fields }).map((_, index) => (
      <div key={index} className="animate-pulse">
        <SkeletonLine width="w-1/4" className="mb-2" />
        <div className="h-10 bg-gray-200 rounded border" />
      </div>
    ))}
    <div className="animate-pulse">
      <div className="h-10 bg-gray-200 rounded w-32" />
    </div>
  </div>
);

export default LoadingSpinner;
