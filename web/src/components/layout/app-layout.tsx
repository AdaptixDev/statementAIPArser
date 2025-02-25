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
    <div className="min-h-screen bg-gray-50">
      <Sidebar isOpen={isSidebarOpen} onClose={closeSidebar} />
      <SidebarTrigger onClick={openSidebar} />
      
      <main className="md:ml-64 min-h-screen p-4 md:p-6 transition-all duration-300">
        <div className="max-w-7xl mx-auto">
          <header className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              Adaptix Innovation Smart Finance
            </h1>
          </header>
          
          {children}
        </div>
      </main>
    </div>
  );
} 