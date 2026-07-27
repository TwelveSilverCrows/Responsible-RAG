'use client';

import { AdminShell } from '@/components/layout/AdminShell';
import { AdminGuard } from '@/components/AuthGuard';
import { AddSourceWizard } from '@/components/admin/AddSourceWizard';

export default function AddSourcePage() {
  return (
    <AdminGuard>
    <AdminShell>
      <AddSourceWizard />
    </AdminShell>
    </AdminGuard>
  );
}
