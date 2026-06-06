import { z } from 'zod/v4';

export const consentSchema = z.object({
  profileMode: z.enum(['full', 'general'], {
    message: 'Please select a privacy mode',
  }),
  researchDataConsent: z.boolean().default(false),
});

export type ConsentFormData = z.infer<typeof consentSchema>;
