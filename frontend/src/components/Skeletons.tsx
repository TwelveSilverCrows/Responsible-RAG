'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

export function MessageListSkeleton() {
  return (
    <div className="space-y-4 p-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[70%] space-y-2 ${i % 2 === 0 ? 'items-end' : 'items-start'}`}>
            <Skeleton className={`h-4 w-${i % 2 === 0 ? '48' : '64'} rounded-lg`} />
            <Skeleton className="h-4 w-full rounded-lg" />
            {i % 2 !== 0 && <Skeleton className="h-16 w-full rounded-lg" />}
          </div>
        </div>
      ))}
    </div>
  );
}

export function SourceTableSkeleton() {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4 mb-4">
        <Skeleton className="h-10 w-64 rounded-lg" />
        <Skeleton className="h-10 w-32 rounded-lg" />
      </div>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center gap-4 p-3">
          <Skeleton className="h-5 w-5 rounded" />
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      ))}
    </div>
  );
}

export function ProfileFormSkeleton() {
  return (
    <div className="space-y-6 max-w-2xl">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-32 rounded" />
          <Skeleton className="h-10 w-full rounded-lg" />
        </div>
      ))}
    </div>
  );
}

export function DashboardCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-4 w-24 rounded" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-16 rounded mb-2" />
        <Skeleton className="h-3 w-32 rounded" />
      </CardContent>
    </Card>
  );
}

export function PageSkeleton() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="space-y-4 w-full max-w-lg p-6">
        <Skeleton className="h-8 w-48 rounded-lg mx-auto" />
        <Skeleton className="h-4 w-full rounded" />
        <Skeleton className="h-4 w-3/4 rounded" />
        <div className="space-y-3 mt-6">
          <Skeleton className="h-10 w-full rounded-lg" />
          <Skeleton className="h-10 w-full rounded-lg" />
          <Skeleton className="h-10 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}
