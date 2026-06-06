import type { ProfileMode } from '@/types/profile';

/**
 * Returns a human-readable description of the current privacy mode
 */
export function getModeDescription(mode: ProfileMode | null): string {
  switch (mode) {
    case 'full':
      return 'Personalized — your profile is used to adapt responses';
    case 'general':
      return 'General mode — no personal data is stored or used';
    default:
      return 'No privacy mode selected';
  }
}

/**
 * Returns the appropriate privacy notice text for the chat input area
 */
export function getChatPrivacyNotice(mode: ProfileMode | null): {
  text: string;
  linkText: string;
  linkHref: string;
} {
  if (mode === 'full') {
    return {
      text: 'Responses are personalized to your profile.',
      linkText: 'Edit profile',
      linkHref: '/profile',
    };
  }
  return {
    text: 'General mode — no personal data is stored or used.',
    linkText: 'Learn more',
    linkHref: '/settings',
  };
}

/**
 * Returns the confirmation message for mode switching
 */
export function getModeSwitchConfirmation(
  from: ProfileMode,
  to: ProfileMode
): { title: string; description: string; isDestructive: boolean } {
  if (from === 'full' && to === 'general') {
    return {
      title: 'Switch to General Mode?',
      description:
        'Your stored profile will be deleted. You will no longer receive personalized responses. This action cannot be undone.',
      isDestructive: true,
    };
  }
  return {
    title: 'Switch to Full Profile Mode?',
    description:
      'You will be asked to complete a profile so the system can personalize responses to your needs.',
    isDestructive: false,
  };
}

/**
 * Formats the profile data as a readable JSON view for the "View my data" feature
 */
export function formatProfileForDisplay(profile: Record<string, unknown>): string {
  const filtered = Object.fromEntries(
    Object.entries(profile).filter(
      ([key]) => !['id', 'userId'].includes(key)
    )
  );
  return JSON.stringify(filtered, null, 2);
}
