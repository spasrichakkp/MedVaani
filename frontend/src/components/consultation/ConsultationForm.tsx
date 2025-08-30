import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useConsultation } from '@/hooks/useConsultation';
import { validationService } from '@/utils/validation';
import { ConsultationRequest } from '@/types/api';
import { GENDER_OPTIONS } from '@/utils/constants';

export interface ConsultationFormData {
  symptoms: string;
  age: string;
  gender: string;
  medicalHistory: string;
}

export interface ConsultationFormProps {
  onSubmit?: (data: ConsultationRequest) => void;
  onSuccess?: (result: any) => void;
  onError?: (error: any) => void;
  disabled?: boolean;
  className?: string;
}

export const ConsultationForm: React.FC<ConsultationFormProps> = ({
  onSubmit,
  onSuccess,
  onError,
  disabled = false,
  className = '',
}) => {
  const [consultationType, setConsultationType] = useState<'text' | 'enhanced'>('text');
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ConsultationFormData>({
    defaultValues: {
      symptoms: '',
      age: '',
      gender: '',
      medicalHistory: '',
    },
  });

  const consultation = useConsultation({
    onSuccess: (result) => {
      reset();
      if (onSuccess) onSuccess(result);
    },
    onError: (error) => {
      if (onError) onError(error);
    },
  });

  const symptoms = watch('symptoms');

  const handleFormSubmit = useCallback(async (data: ConsultationFormData) => {
    // Validate form data
    const validationResult = validationService.validateConsultationForm({
      symptoms: data.symptoms,
      age: data.age,
      gender: data.gender,
      medicalHistory: data.medicalHistory,
    });

    if (!validationResult.isValid) {
      console.error('Validation errors:', validationResult.errors);
      return;
    }

    // Prepare consultation request
    const consultationData: ConsultationRequest = {
      symptoms: validationService.sanitizeText(data.symptoms),
      patient_age: data.age ? parseInt(data.age, 10) : undefined,
      patient_gender: data.gender || undefined,
      medical_history: data.medicalHistory ? validationService.sanitizeText(data.medicalHistory) : undefined,
    };

    // Call custom onSubmit if provided
    if (onSubmit) {
      onSubmit(consultationData);
      return;
    }

    // Submit consultation
    try {
      if (consultationType === 'enhanced') {
        await consultation.submitEnhancedConsultation(consultationData);
      } else {
        await consultation.submitTextConsultation(consultationData);
      }
    } catch (error) {
      console.error('Consultation submission failed:', error);
    }
  }, [consultationType, consultation, onSubmit]);

  const isLoading = consultation.isLoading;
  const isFormDisabled = disabled || isLoading;

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Medical Consultation
        </h2>
        <p className="text-gray-600 text-sm">
          Please describe your symptoms and provide any relevant medical information.
        </p>
      </div>

      {/* Consultation Type Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Consultation Type
        </label>
        <div className="flex space-x-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="text"
              checked={consultationType === 'text'}
              onChange={(e) => setConsultationType(e.target.value as 'text')}
              disabled={isFormDisabled}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Standard Consultation</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="enhanced"
              checked={consultationType === 'enhanced'}
              onChange={(e) => setConsultationType(e.target.value as 'enhanced')}
              disabled={isFormDisabled}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Enhanced Consultation</span>
          </label>
        </div>
      </div>

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        {/* Symptoms */}
        <div>
          <label htmlFor="symptoms" className="block text-sm font-medium text-gray-700 mb-2">
            Describe your symptoms *
          </label>
          <textarea
            id="symptoms"
            rows={4}
            disabled={isFormDisabled}
            className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.symptoms ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Please describe your symptoms in detail..."
            {...register('symptoms', {
              required: 'Please describe your symptoms',
              minLength: {
                value: 10,
                message: 'Please provide more details (at least 10 characters)',
              },
              maxLength: {
                value: 2000,
                message: 'Description is too long (maximum 2000 characters)',
              },
            })}
          />
          {errors.symptoms && (
            <p className="mt-1 text-sm text-red-600">{errors.symptoms.message}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            {symptoms?.length || 0}/2000 characters
          </p>
        </div>

        {/* Patient Demographics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Age */}
          <div>
            <label htmlFor="age" className="block text-sm font-medium text-gray-700 mb-2">
              Age
            </label>
            <input
              id="age"
              type="number"
              min="0"
              max="150"
              disabled={isFormDisabled}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.age ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter your age"
              {...register('age', {
                min: {
                  value: 0,
                  message: 'Age cannot be negative',
                },
                max: {
                  value: 150,
                  message: 'Age cannot exceed 150',
                },
              })}
            />
            {errors.age && (
              <p className="mt-1 text-sm text-red-600">{errors.age.message}</p>
            )}
          </div>

          {/* Gender */}
          <div>
            <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-2">
              Gender
            </label>
            <select
              id="gender"
              disabled={isFormDisabled}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.gender ? 'border-red-500' : 'border-gray-300'
              }`}
              {...register('gender')}
            >
              <option value="">Select gender (optional)</option>
              {GENDER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.gender && (
              <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>
            )}
          </div>
        </div>

        {/* Medical History */}
        <div>
          <label htmlFor="medicalHistory" className="block text-sm font-medium text-gray-700 mb-2">
            Medical History
          </label>
          <textarea
            id="medicalHistory"
            rows={3}
            disabled={isFormDisabled}
            className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.medicalHistory ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Any relevant medical history, current medications, allergies..."
            {...register('medicalHistory', {
              maxLength: {
                value: 1000,
                message: 'Medical history is too long (maximum 1000 characters)',
              },
            })}
          />
          {errors.medicalHistory && (
            <p className="mt-1 text-sm text-red-600">{errors.medicalHistory.message}</p>
          )}
        </div>

        {/* Error Display */}
        {consultation.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="text-red-400 mr-3">⚠️</div>
              <div>
                <h3 className="text-sm font-medium text-red-800">
                  Consultation Failed
                </h3>
                <p className="mt-1 text-sm text-red-700">
                  {consultation.error.message}
                </p>
                {consultation.retry && (
                  <button
                    type="button"
                    onClick={consultation.retry}
                    className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
                  >
                    Try again
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end">
          <Button
            type="submit"
            loading={isLoading}
            loadingText="Analyzing..."
            disabled={isFormDisabled}
            size="lg"
            className="min-w-32"
          >
            {consultationType === 'enhanced' ? 'Start Enhanced Analysis' : 'Analyze Symptoms'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ConsultationForm;
