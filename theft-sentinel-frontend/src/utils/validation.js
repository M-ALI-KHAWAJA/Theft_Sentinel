/**
 * Professional form validation utilities
 */

/**
 * Validates email format
 * Rules:
 * - Must start with alphabets
 * - May contain numbers or underscores after start
 * - No special symbols allowed (except _)
 * - Must end with @gmail.com
 */
export const validateEmail = (email) => {
  if (!email || email.trim() === '') {
    return { valid: false, message: 'Email is required' };
  }

  const trimmed = email.trim();
  
  // Check for leading/trailing spaces
  if (trimmed !== email) {
    return { valid: false, message: 'Email cannot have leading or trailing spaces' };
  }

  // Must start with alphabet
  if (!/^[a-zA-Z]/.test(trimmed)) {
    return { valid: false, message: 'Email must start with a letter' };
  }

  // Must end with @gmail.com
  if (!trimmed.endsWith('@gmail.com')) {
    return { valid: false, message: 'Email must end with @gmail.com' };
  }

  // Extract local part (before @)
  const localPart = trimmed.split('@')[0];
  
  // Local part can only contain letters, numbers, and underscores
  if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(localPart)) {
    return { valid: false, message: 'Email can only contain letters, numbers, and underscores after the first letter' };
  }

  // Minimum length check (at least 1 char + @gmail.com = 11 chars minimum)
  if (trimmed.length < 11) {
    return { valid: false, message: 'Email is too short' };
  }

  // Maximum length check (reasonable limit)
  if (trimmed.length > 100) {
    return { valid: false, message: 'Email is too long' };
  }

  return { valid: true, message: '' };
};

/**
 * Validates username format
 * Rules:
 * - Must start with alphabets
 * - May contain numbers and underscores
 * - No spaces
 * - No special characters
 */
export const validateUsername = (username) => {
  if (!username || username.trim() === '') {
    return { valid: false, message: 'Username is required' };
  }

  const trimmed = username.trim();
  
  // Check for leading/trailing spaces
  if (trimmed !== username) {
    return { valid: false, message: 'Username cannot have leading or trailing spaces' };
  }

  // Minimum length
  if (trimmed.length < 3) {
    return { valid: false, message: 'Username must be at least 3 characters long' };
  }

  // Maximum length
  if (trimmed.length > 30) {
    return { valid: false, message: 'Username must be less than 30 characters' };
  }

  // Must start with alphabet
  if (!/^[a-zA-Z]/.test(trimmed)) {
    return { valid: false, message: 'Username must start with a letter' };
  }

  // Can only contain letters, numbers, and underscores
  if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(trimmed)) {
    return { valid: false, message: 'Username can only contain letters, numbers, and underscores' };
  }

  return { valid: true, message: '' };
};

/**
 * Validates password strength
 * Rules:
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 */
export const validatePassword = (password) => {
  if (!password || password.trim() === '') {
    return { valid: false, message: 'Password is required' };
  }

  // Check for leading/trailing spaces
  if (password.trim() !== password) {
    return { valid: false, message: 'Password cannot have leading or trailing spaces' };
  }

  // Minimum length
  if (password.length < 8) {
    return { valid: false, message: 'Password must be at least 8 characters long' };
  }

  // Maximum length (reasonable limit)
  if (password.length > 128) {
    return { valid: false, message: 'Password is too long (maximum 128 characters)' };
  }

  // At least one uppercase letter
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter' };
  }

  // At least one lowercase letter
  if (!/[a-z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one lowercase letter' };
  }

  // At least one number
  if (!/[0-9]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one number' };
  }

  return { valid: true, message: '' };
};

/**
 * Validates that two passwords match
 */
export const validatePasswordMatch = (password, confirmPassword) => {
  if (!confirmPassword || confirmPassword.trim() === '') {
    return { valid: false, message: 'Please confirm your password' };
  }

  if (password !== confirmPassword) {
    return { valid: false, message: 'Passwords do not match' };
  }

  return { valid: true, message: '' };
};

/**
 * Trims input value to remove leading/trailing spaces
 */
export const trimInput = (value) => {
  return typeof value === 'string' ? value.trim() : value;
};

