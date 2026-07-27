export type AgeRange = 'under_18' | '18_30' | '31_50' | '51_65' | '65_plus' | 'prefer_not_to_say';

export type DisabilityType = 'visual' | 'hearing' | 'cognitive' | 'mobility' | 'mental_health' | 'none' | 'prefer_not_to_say';

export type ImmigrationStatus = 'citizen' | 'permanent_resident' | 'temporary_resident' | 'refugee' | 'undocumented' | 'prefer_not_to_say';

export type IndigenousIdentity = 'first_nations' | 'metis' | 'inuit' | 'non_indigenous' | 'prefer_not_to_say';

export type EducationLevel = 'no_formal' | 'high_school' | 'some_college' | 'bachelors' | 'masters' | 'doctoral' | 'prefer_not_to_say';

export type ProfileMode = 'full' | 'general';

export interface UserProfile {
  id: string;
  userId: string;
  preferredName: string;
  ageRange: AgeRange | null;
  genderIdentity: string[];
  pronouns: string | null;
  primaryLanguage: string | null;
  disability: DisabilityType[];
  immigrationStatus: ImmigrationStatus | null;
  indigenousIdentity: IndigenousIdentity | null;
  educationLevel: EducationLevel | null;
  literacyComfortAI: number; // 1-5
  profileMode: ProfileMode;
  createdAt: string;
  updatedAt: string;
}

export const AGE_RANGE_OPTIONS: { value: AgeRange; label: string }[] = [
  { value: 'under_18', label: 'Under 18' },
  { value: '18_30', label: '18–30' },
  { value: '31_50', label: '31–50' },
  { value: '51_65', label: '51–65' },
  { value: '65_plus', label: '65+' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
];

export const DISABILITY_OPTIONS: { value: DisabilityType; label: string; description: string }[] = [
  { value: 'visual', label: 'Visual', description: 'Difficulty seeing, even with glasses or contacts' },
  { value: 'hearing', label: 'Hearing', description: 'Difficulty hearing, even with hearing aids' },
  { value: 'cognitive', label: 'Cognitive', description: 'Difficulty remembering, concentrating, or making decisions' },
  { value: 'mobility', label: 'Mobility', description: 'Difficulty walking, climbing stairs, or moving around' },
  { value: 'mental_health', label: 'Mental health', description: 'Mental health condition that affects daily activities' },
  { value: 'none', label: 'None', description: 'No disability or accessibility needs' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say', description: '' },
];

export const IMMIGRATION_OPTIONS: { value: ImmigrationStatus; label: string }[] = [
  { value: 'citizen', label: 'Citizen' },
  { value: 'permanent_resident', label: 'Permanent resident' },
  { value: 'temporary_resident', label: 'Temporary resident (e.g., work/study permit)' },
  { value: 'refugee', label: 'Refugee or asylum seeker' },
  { value: 'undocumented', label: 'Undocumented' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
];

export const INDIGENOUS_OPTIONS: { value: IndigenousIdentity; label: string }[] = [
  { value: 'first_nations', label: 'First Nations' },
  { value: 'metis', label: 'Métis' },
  { value: 'inuit', label: 'Inuit' },
  { value: 'non_indigenous', label: 'Non-Indigenous' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
];

export const EDUCATION_OPTIONS: { value: EducationLevel; label: string }[] = [
  { value: 'no_formal', label: 'No formal education' },
  { value: 'high_school', label: 'High school diploma' },
  { value: 'some_college', label: 'Some college or trade school' },
  { value: 'bachelors', label: "Bachelor's degree" },
  { value: 'masters', label: "Master's degree" },
  { value: 'doctoral', label: 'Doctoral degree' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
];

export const LANGUAGE_OPTIONS = [
  'English', 'French', 'Spanish', 'Mandarin', 'Cantonese', 'Punjabi',
  'Arabic', 'Tagalog', 'Hindi', 'Urdu', 'Portuguese', 'German',
  'Italian', 'Vietnamese', 'Korean', 'Russian', 'Japanese', 'Other',
];

export const GENDER_OPTIONS: { value: string; label: string }[] = [
  { value: 'Man', label: 'Man' },
  { value: 'Woman', label: 'Woman' },
  { value: 'Non-binary', label: 'Non-binary' },
  { value: 'Genderqueer', label: 'Genderqueer' },
  { value: 'Two-Spirit', label: 'Two-Spirit' },
  { value: 'Prefer not to say', label: 'Prefer not to say' },
];

export const COMFORT_LABELS: Record<number, string> = {
  1: 'Not comfortable',
  2: 'Slightly comfortable',
  3: 'Somewhat comfortable',
  4: 'Comfortable',
  5: 'Very comfortable',
};
