import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Providers } from '@/components/Providers';

// Lazy-load pages for better performance
import { lazy, Suspense } from 'react';

const Home = lazy(() => import('@/app/page'));
const LoginPage = lazy(() => import('@/app/login/page'));
const RegisterPage = lazy(() => import('@/app/register/page'));
const VerifyEmailPage = lazy(() => import('@/app/auth/verify-email/page'));
const AuthCallbackPage = lazy(() => import('@/app/auth/callback/page'));
const ResetPasswordPage = lazy(() => import('@/app/auth/reset-password/page'));
const ChatPage = lazy(() => import('@/app/chat/page'));
const ConversationPage = lazy(() => import('@/app/chat/[conversationId]/page'));
const OnboardingWelcome = lazy(() => import('@/app/onboarding/welcome/page'));
const OnboardingConsent = lazy(() => import('@/app/onboarding/consent/page'));
const OnboardingProfile = lazy(() => import('@/app/onboarding/profile/page'));
const ProfilePage = lazy(() => import('@/app/profile/page'));
const SettingsPage = lazy(() => import('@/app/settings/page'));
const FeedbackPage = lazy(() => import('@/app/feedback/page'));
const AdminDashboardPage = lazy(() => import('@/app/admin/page'));
const SourcesLibraryPage = lazy(() => import('@/app/admin/sources/page'));
const AddSourcePage = lazy(() => import('@/app/admin/sources/new/page'));
const SourceDetailPage = lazy(() => import('@/app/admin/sources/[id]/page'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex items-center gap-2 text-muted-foreground text-sm">
        <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        Loading…
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Providers>
      <ErrorBoundary>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/auth/verify-email" element={<VerifyEmailPage />} />
              <Route path="/auth/callback" element={<AuthCallbackPage />} />
              <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
              <Route path="/chat" element={<ChatPage />} />
                <Route path="/chat/:conversationId" element={<ConversationPage />} />
                <Route path="/onboarding/welcome" element={<OnboardingWelcome />} />
                <Route path="/onboarding/consent" element={<OnboardingConsent />} />
                <Route path="/onboarding/profile" element={<OnboardingProfile />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/feedback" element={<FeedbackPage />} />
                <Route path="/admin" element={<AdminDashboardPage />} />
                <Route path="/admin/sources" element={<SourcesLibraryPage />} />
                <Route path="/admin/sources/new" element={<AddSourcePage />} />
                <Route path="/admin/sources/:id" element={<SourceDetailPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
          <Toaster richColors position="bottom-right" />
        </ErrorBoundary>
    </Providers>
  );
}
