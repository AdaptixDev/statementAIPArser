"use client"

import * as React from "react"

interface SwitchProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  id?: string;
  className?: string;
}

export function Switch({ checked, onCheckedChange, id, className = "" }: SwitchProps) {
  return (
    <div 
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? 'bg-blue-600' : 'bg-gray-200'
      } ${className}`}
      onClick={() => onCheckedChange(!checked)}
    >
      <span 
        className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-5' : 'translate-x-1'
        }`} 
      />
      {id && (
        <input
          type="checkbox"
          id={id}
          checked={checked}
          onChange={() => onCheckedChange(!checked)}
          className="sr-only"
        />
      )}
    </div>
  )
} 