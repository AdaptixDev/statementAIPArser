"use client";

import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { 
  FileText, 
  CreditCard,
  User,
  Menu,
  X
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ className, isOpen, onClose, ...props }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden" 
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 w-64 bg-gray-900 text-white p-4 transition-transform duration-300 ease-in-out transform",
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          className
        )}
        {...props}
      >
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-xl font-bold">Adaptix Innovation</h1>
          <Button 
            variant="ghost" 
            size="icon" 
            className="md:hidden text-white" 
            onClick={onClose}
          >
            <X className="size-5" />
          </Button>
        </div>
        
        <nav className="space-y-6">
          {/* Finance Section */}
          <div>
            <h2 className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              Finance
            </h2>
            <div className="space-y-1">
              <SidebarItem href="/statements" icon={<CreditCard className="size-5" />}>
                Bank Statements
              </SidebarItem>
            </div>
          </div>

          {/* Personal Section */}
          <div>
            <h2 className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              Personal
            </h2>
            <div className="space-y-1">
              <SidebarItem href="/documents" icon={<FileText className="size-5" />}>
                Documents
              </SidebarItem>
              <SidebarItem href="/identification" icon={<User className="size-5" />}>
                Identification
              </SidebarItem>
            </div>
          </div>
        </nav>
        
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-gray-800 p-3 rounded-lg">
            <p className="text-sm text-gray-400">Smart Finance</p>
            <p className="text-xs text-gray-500 mt-1">v1.0.0</p>
          </div>
        </div>
      </div>
    </>
  );
}

interface SidebarItemProps {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

function SidebarItem({ href, icon, children }: SidebarItemProps) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}

export function SidebarTrigger({ 
  onClick, 
  className 
}: { 
  onClick: () => void;
  className?: string;
}) {
  return (
    <Button 
      variant="ghost" 
      size="icon" 
      className={cn("md:hidden", className)} 
      onClick={onClick}
    >
      <Menu className="size-5" />
    </Button>
  );
} 