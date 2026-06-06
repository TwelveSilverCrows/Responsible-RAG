import { z } from 'zod/v4';

export const profileSchema = z.object({
  preferredName: z.string().min(1, 'Preferred name is required').max(50, 'Name is too long'),
  ageRange: z.enum(['under_18', '18_30', '31_50', '51_65', '65_plus', 'prefer_not_to_say']).nullable().optional(),
  genderIdentity: z.array(z.string()).optional(),
  pronouns: z.string().max(50).nullable().optional(),
  primaryLanguage: z.string().nullable().optional(),
  disability: z.array(z.enum(['visual', 'hearing', 'cognitive', 'mobility', 'mental_health', 'none', 'prefer_not_to_say'])).optional(),
  immigrationStatus: z.enum(['citizen', 'permanent_resident', 'temporary_resident', 'refugee', 'undocumented', 'prefer_not_to_say']).nullable().optional(),
  indigenousIdentity: z.enum(['first_nations', 'metis', 'inuit', 'non_indigenous', 'prefer_not_to_say']).nullable().optional(),
  educationLevel: z.enum(['no_formal', 'high_school', 'some_college', 'bachelors', 'masters', 'doctoral', 'prefer_not_to_say']).nullable().optional(),
  literacyComfortAI: z.number().min(1).max(5).optional(),
});

export type ProfileFormData = z.infer<typeof profileSchema>;

export const loginSchema = z.object({
  email: z.email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    displayName: z.string().min(1, 'Display name is required').max(50, 'Name is too long'),
    email: z.email('Please enter a valid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(8, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;

export const resetPasswordSchema = z.object({
  email: z.email('Please enter a valid email address'),
});

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export const newPasswordSchema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(8, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export type NewPasswordFormData = z.infer<typeof newPasswordSchema>;
