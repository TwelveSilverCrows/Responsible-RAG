'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Database,
  User,
  Settings,
  LogOut,
  Menu,
  Shield,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

const adminNavItems = [
  { href: '/admin', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { href: '/admin/sources', label: 'Sources', icon: Database },
];

function AdminSidebarContent({
  activeRoute,
  onNavigate,
}: {
  activeRoute: string;
  onNavigate?: () => void;
}) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 p-4 border-b">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
          <Shield className="w-4 h-4 text-primary-foreground" />
        </div>
        <div>
          <span className="text-lg font-display font-semibold block leading-tight">Responsible AI</span>
          <span className="text-xs text-muted-foreground">Admin Panel</span>
        </div>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {adminNavItems.map((item) => {
          const isActive = item.exact
            ? activeRoute === item.href
            : activeRoute.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const initials = user?.displayName
    ? user.displayName
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'A';

  return (
    <div className="min-h-screen flex">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-64 border-r bg-sidebar">
        <AdminSidebarContent activeRoute={pathname} />
      </aside>

      {/* Mobile sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-64">
          <AdminSidebarContent
            activeRoute={pathname}
            onNavigate={() => setMobileOpen(false)}
          />
        </SheetContent>
      </Sheet>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-14 border-b bg-card flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </Button>
            <span className="text-sm text-muted-foreground">Admin</span>
          </div>
          <div className="flex items-center gap-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 px-2">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-primary/10 text-primary text-sm">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden sm:inline text-sm font-medium">
                    {user?.displayName || 'Admin'}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem asChild>
                  <Link href="/settings" className="flex items-center gap-2">
                    <Settings className="w-4 h-4" /> Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/chat" className="flex items-center gap-2">
                    <User className="w-4 h-4" /> Switch to Chat
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
                  <LogOut className="w-4 h-4 mr-2" /> Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}
