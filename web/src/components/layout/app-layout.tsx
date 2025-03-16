"use client";

import * as React from "react";
import { Sidebar, SidebarTrigger } from "@/components/layout/sidebar";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);

  const openSidebar = () => setIsSidebarOpen(true);
  const closeSidebar = () => setIsSidebarOpen(false);

  return (
    <div className="min-h-screen-dynamic bg-gray-50">
      <Sidebar isOpen={isSidebarOpen} onClose={closeSidebar} />
      <SidebarTrigger onClick={openSidebar} className="fixed top-4 left-4 z-50 md:hidden" />
      
      <main className="w-full min-h-screen-dynamic px-4 py-safe-top pb-safe-bottom transition-all duration-300 md:ml-64 md:px-6">
        <div className="w-full max-w-mobile md:max-w-7xl mx-auto">
          <header className="sticky top-0 z-40 py-4 mb-4 bg-gray-50/80 backdrop-blur-sm">
            <h1 className="text-xl font-bold text-gray-900 md:text-2xl truncate">
              Adaptix Innovation Smart Finance
            </h1>
          </header>
          
          <div className="pb-20 md:pb-6">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
} 