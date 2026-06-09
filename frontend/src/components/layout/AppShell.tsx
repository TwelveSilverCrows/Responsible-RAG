'use client';

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  MessageSquare,
  User,
  Settings,
  LogOut,
  Menu,
  Shield,
  ChevronLeft,
  ChevronRight,
  MessageCircle,
  Database,
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
import { ProfileModeBadge } from '@/components/chat/ProfileModeBadge';
import { useTheme } from '@/lib/themeProvider';
import { Sun, Moon } from 'lucide-react';

const clientNavItems = [
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/profile', label: 'Profile', icon: User },
  { href: '/settings', label: 'Settings', icon: Settings },
  { href: '/feedback', label: 'Feedback', icon: MessageCircle },
];

const adminNavItem = { href: '/admin', label: 'Admin', icon: Database };

function SidebarContent({
  activeRoute,
  onNavigate,
  collapsed,
}: {
  activeRoute: string;
  onNavigate?: () => void;
  collapsed?: boolean;
}) {
  const { user, isAdmin } = useAuth();

  const navItems = isAdmin
    ? [...clientNavItems, adminNavItem]
    : clientNavItems;

  return (
    <div className="flex flex-col h-full">
      <div className={cn('flex items-center gap-2 p-4 border-b', collapsed && 'justify-center')}>
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
          <Shield className="w-4 h-4 text-primary-foreground" />
        </div>
        {!collapsed && (
          <span className="text-lg font-display font-semibold truncate">Responsible AI</span>
        )}
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => {
          const isActive = activeRoute.startsWith(item.href);
          return (
            <Link
              key={item.href}
              to={item.href}
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                collapsed && 'justify-center px-2'
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>
      <div className={cn('p-3 border-t', collapsed && 'flex justify-center')}>
        <ProfileModeBadge variant="sidebar" />
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const initials = user?.displayName
    ? user.displayName
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Desktop sidebar */}
      <aside
        className={cn(
          'hidden md:flex flex-col border-r bg-sidebar transition-all duration-300',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        <SidebarContent activeRoute={pathname} collapsed={collapsed} />
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute top-20 -right-3 w-6 h-6 bg-card border rounded-full flex items-center justify-center shadow-sm hover:bg-accent z-10 hidden md:flex"
          style={{ left: collapsed ? '52px' : '244px' }}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
        </button>
      </aside>

      {/* Mobile sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-64">
          <SidebarContent
            activeRoute={pathname}
            onNavigate={() => setMobileOpen(false)}
          />
        </SheetContent>
      </Sheet>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="h-14 border-b bg-card flex items-center justify-between px-4 flex-shrink-0">
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
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              className="text-muted-foreground hover:text-foreground"
            >
              {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 px-2">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-primary/10 text-primary text-sm">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden sm:inline text-sm font-medium">
                    {user?.displayName || 'User'}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem asChild>
                  <Link to="/profile" className="flex items-center gap-2">
                    <User className="w-4 h-4" /> Profile
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/settings" className="flex items-center gap-2">
                    <Settings className="w-4 h-4" /> Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/feedback" className="flex items-center gap-2">
                    <MessageCircle className="w-4 h-4" /> Feedback
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
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
