import { VALIDATION_RULES, GENDER_OPTIONS } from './constants';

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export interface FieldValidationResult {
  isValid: boolean;
  error?: string;
}

class ValidationService {
  // Validate symptoms text
  validateSymptoms(symptoms: string): FieldValidationResult {
    if (!symptoms || symptoms.trim().length === 0) {
      return {
        isValid: false,
        error: 'Please describe your symptoms',
      };
    }

    const trimmedSymptoms = symptoms.trim();

    if (trimmedSymptoms.length < VALIDATION_RULES.SYMPTOMS.MIN_LENGTH) {
      return {
        isValid: false,
        error: `Please provide more details (at least ${VALIDATION_RULES.SYMPTOMS.MIN_LENGTH} characters)`,
      };
    }

    if (trimmedSymptoms.length > VALIDATION_RULES.SYMPTOMS.MAX_LENGTH) {
      return {
        isValid: false,
        error: `Description is too long (maximum ${VALIDATION_RULES.SYMPTOMS.MAX_LENGTH} characters)`,
      };
    }

    return { isValid: true };
  }

  // Validate patient age
  validateAge(age: string | number): FieldValidationResult {
    if (!age && age !== 0) {
      return { isValid: true }; // Age is optional
    }

    const numericAge = typeof age === 'string' ? parseInt(age, 10) : age;

    if (isNaN(numericAge)) {
      return {
        isValid: false,
        error: 'Please enter a valid age',
      };
    }

    if (numericAge < VALIDATION_RULES.PATIENT_AGE.MIN) {
      return {
        isValid: false,
        error: 'Age cannot be negative',
      };
    }

    if (numericAge > VALIDATION_RULES.PATIENT_AGE.MAX) {
      return {
        isValid: false,
        error: `Age cannot exceed ${VALIDATION_RULES.PATIENT_AGE.MAX}`,
      };
    }

    return { isValid: true };
  }

  // Validate gender
  validateGender(gender: string): FieldValidationResult {
    if (!gender) {
      return { isValid: true }; // Gender is optional
    }

    const validGenders = GENDER_OPTIONS.map(option => option.value);
    if (!validGenders.includes(gender)) {
      return {
        isValid: false,
        error: 'Please select a valid gender option',
      };
    }

    return { isValid: true };
  }

  // Validate medical history
  validateMedicalHistory(history: string): FieldValidationResult {
    if (!history) {
      return { isValid: true }; // Medical history is optional
    }

    if (history.length > VALIDATION_RULES.MEDICAL_HISTORY.MAX_LENGTH) {
      return {
        isValid: false,
        error: `Medical history is too long (maximum ${VALIDATION_RULES.MEDICAL_HISTORY.MAX_LENGTH} characters)`,
      };
    }

    return { isValid: true };
  }

  // Validate email format
  validateEmail(email: string): FieldValidationResult {
    if (!email) {
      return { isValid: true }; // Email is optional in most cases
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return {
        isValid: false,
        error: 'Please enter a valid email address',
      };
    }

    return { isValid: true };
  }

  // Validate phone number
  validatePhone(phone: string): FieldValidationResult {
    if (!phone) {
      return { isValid: true }; // Phone is optional
    }

    // Basic phone validation - adjust regex based on your requirements
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    if (!phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''))) {
      return {
        isValid: false,
        error: 'Please enter a valid phone number',
      };
    }

    return { isValid: true };
  }

  // Validate audio file
  validateAudioFile(file: File): FieldValidationResult {
    if (!file) {
      return {
        isValid: false,
        error: 'Please select an audio file',
      };
    }

    // Check file size
    if (file.size > VALIDATION_RULES.AUDIO.MAX_SIZE) {
      const maxSizeMB = VALIDATION_RULES.AUDIO.MAX_SIZE / (1024 * 1024);
      return {
        isValid: false,
        error: `File size too large (maximum ${maxSizeMB}MB)`,
      };
    }

    // Check file type
    const isValidType = VALIDATION_RULES.AUDIO.SUPPORTED_FORMATS.some(format =>
      file.type.startsWith(format.split(';')[0])
    );

    if (!isValidType) {
      return {
        isValid: false,
        error: 'Unsupported audio format. Please use WebM, MP4, MP3, or WAV.',
      };
    }

    return { isValid: true };
  }

  // Validate consultation form data
  validateConsultationForm(data: {
    symptoms: string;
    age?: string | number;
    gender?: string;
    medicalHistory?: string;
  }): ValidationResult {
    const errors: string[] = [];

    // Validate symptoms
    const symptomsResult = this.validateSymptoms(data.symptoms);
    if (!symptomsResult.isValid && symptomsResult.error) {
      errors.push(symptomsResult.error);
    }

    // Validate age
    if (data.age !== undefined) {
      const ageResult = this.validateAge(data.age);
      if (!ageResult.isValid && ageResult.error) {
        errors.push(ageResult.error);
      }
    }

    // Validate gender
    if (data.gender) {
      const genderResult = this.validateGender(data.gender);
      if (!genderResult.isValid && genderResult.error) {
        errors.push(genderResult.error);
      }
    }

    // Validate medical history
    if (data.medicalHistory) {
      const historyResult = this.validateMedicalHistory(data.medicalHistory);
      if (!historyResult.isValid && historyResult.error) {
        errors.push(historyResult.error);
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }

  // Sanitize input text
  sanitizeText(text: string): string {
    if (!text) return '';
    
    return text
      .trim()
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .replace(/[<>]/g, ''); // Remove potential HTML tags
  }

  // Check if string contains only whitespace
  isEmptyOrWhitespace(text: string): boolean {
    return !text || text.trim().length === 0;
  }

  // Validate required field
  validateRequired(value: any, fieldName: string): FieldValidationResult {
    if (value === null || value === undefined || this.isEmptyOrWhitespace(String(value))) {
      return {
        isValid: false,
        error: `${fieldName} is required`,
      };
    }
    return { isValid: true };
  }

  // Validate string length
  validateLength(
    text: string,
    minLength: number,
    maxLength: number,
    fieldName: string
  ): FieldValidationResult {
    if (!text) {
      return {
        isValid: false,
        error: `${fieldName} is required`,
      };
    }

    if (text.length < minLength) {
      return {
        isValid: false,
        error: `${fieldName} must be at least ${minLength} characters`,
      };
    }

    if (text.length > maxLength) {
      return {
        isValid: false,
        error: `${fieldName} cannot exceed ${maxLength} characters`,
      };
    }

    return { isValid: true };
  }

  // Validate numeric range
  validateNumericRange(
    value: number,
    min: number,
    max: number,
    fieldName: string
  ): FieldValidationResult {
    if (value < min) {
      return {
        isValid: false,
        error: `${fieldName} must be at least ${min}`,
      };
    }

    if (value > max) {
      return {
        isValid: false,
        error: `${fieldName} cannot exceed ${max}`,
      };
    }

    return { isValid: true };
  }
}

// Export singleton instance
export const validationService = new ValidationService();
export default validationService;
