import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import { LoadingSpinner } from './LoadingSpinner';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  loadingText?: string;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantClasses = {
  primary: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 text-white border-transparent',
  secondary: 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500 text-white border-transparent',
  success: 'bg-green-600 hover:bg-green-700 focus:ring-green-500 text-white border-transparent',
  danger: 'bg-red-600 hover:bg-red-700 focus:ring-red-500 text-white border-transparent',
  warning: 'bg-orange-600 hover:bg-orange-700 focus:ring-orange-500 text-white border-transparent',
  ghost: 'bg-transparent hover:bg-gray-50 focus:ring-gray-500 text-gray-700 border-gray-300',
};

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

const disabledClasses = 'opacity-50 cursor-not-allowed';

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      loading = false,
      loadingText,
      fullWidth = false,
      leftIcon,
      rightIcon,
      disabled,
      className = '',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    const baseClasses = [
      'inline-flex items-center justify-center',
      'border font-medium rounded-md',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'transition-colors duration-200',
      'disabled:opacity-50 disabled:cursor-not-allowed',
    ].join(' ');

    const classes = [
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      fullWidth ? 'w-full' : '',
      isDisabled ? disabledClasses : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        className={classes}
        disabled={isDisabled}
        {...props}
      >
        {loading && <LoadingSpinner size="sm" color="white" className="mr-2" />}
        {!loading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        
        <span>
          {loading && loadingText ? loadingText : children}
        </span>
        
        {!loading && rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';

// Specialized button components
export const PrimaryButton: React.FC<Omit<ButtonProps, 'variant'>> = (props) => (
  <Button variant="primary" {...props} />
);

export const SecondaryButton: React.FC<Omit<ButtonProps, 'variant'>> = (props) => (
  <Button variant="secondary" {...props} />
);

export const SuccessButton: React.FC<Omit<ButtonProps, 'variant'>> = (props) => (
  <Button variant="success" {...props} />
);

export const DangerButton: React.FC<Omit<ButtonProps, 'variant'>> = (props) => (
  <Button variant="danger" {...props} />
);

export const WarningButton: React.FC<Omit<ButtonProps, 'variant'>> = (props) => (
  <Button variant="warning" {...props} />
);

export const GhostButton: React.FC<Omit<ButtonProps, 'variant'>> = (props) => (
  <Button variant="ghost" {...props} />
);

// Icon button component
export interface IconButtonProps extends Omit<ButtonProps, 'leftIcon' | 'rightIcon'> {
  icon: React.ReactNode;
  'aria-label': string;
}

export const IconButton: React.FC<IconButtonProps> = ({ icon, children, ...props }) => (
  <Button {...props}>
    {icon}
    {children && <span className="sr-only">{children}</span>}
  </Button>
);

export default Button;
