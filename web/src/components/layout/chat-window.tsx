"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Send, RefreshCw, Upload } from "lucide-react";
import { Input } from "../../components/ui/input";

interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  isProcessing?: boolean;
}

interface ChatWindowProps {
  title: string;
  messages: Array<ChatMessage>;
  onSendMessage?: (message: string) => void;
  onRefresh?: () => void;
  onFileUpload?: (file: File) => void;
  onMultipleFilesUpload?: (files: File[]) => void;
}

export function ChatWindow({ title, messages, onSendMessage, onRefresh, onFileUpload, onMultipleFilesUpload }: ChatWindowProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const messagesContainerRef = React.useRef<HTMLDivElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [inputValue, setInputValue] = React.useState("");
  const [lastScrollPosition, setLastScrollPosition] = React.useState(0);
  const [autoScrollEnabled, setAutoScrollEnabled] = React.useState(true);

  // Only scroll to bottom on new messages if auto-scroll is enabled
  React.useEffect(() => {
    if (autoScrollEnabled && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, autoScrollEnabled]);

  // Handle scroll events to detect when user manually scrolls
  const handleScroll = () => {
    if (!messagesContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    
    // Detect if user is scrolling up or down
    const isScrollingUp = scrollTop < lastScrollPosition;
    setLastScrollPosition(scrollTop);
    
    // Check if we're at the bottom of the scroll container
    const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 10;
    
    // If user scrolls up, disable auto-scroll
    if (isScrollingUp && !isAtBottom) {
      setAutoScrollEnabled(false);
    }
    
    // If user scrolls to the bottom, enable auto-scroll again
    if (isAtBottom) {
      setAutoScrollEnabled(true);
    }
  };

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    if (files.length === 1 && onFileUpload) {
      // Single file upload
      onFileUpload(files[0]);
    } else if (files.length > 1 && onMultipleFilesUpload) {
      // Multiple files upload
      const fileArray = Array.from(files);
      onMultipleFilesUpload(fileArray);
    }
  };

  // Reset auto-scroll when user sends a message
  const handleSendMessage = () => {
    if (inputValue.trim() && onSendMessage) {
      onSendMessage(inputValue);
      setInputValue("");
      setAutoScrollEnabled(true);
      
      // Force scroll to bottom
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="h-[calc(100vh-8rem)] md:h-[600px] flex flex-col">
      <CardHeader className="px-4 py-3 border-b">
        <CardTitle className="text-lg font-medium">{title}</CardTitle>
      </CardHeader>
      
      <CardContent 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
        onScroll={handleScroll}
      >
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] md:max-w-[70%] rounded-lg px-4 py-2 ${
                message.isUser
                  ? 'bg-blue-600 text-white'
                  : message.isProcessing
                  ? 'processing-message'
                  : 'bg-gray-100'
              }`}
            >
              <p className="text-sm md:text-base whitespace-pre-wrap break-words">
                {message.content}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </CardContent>

      <CardFooter className="p-4 border-t space-x-2">
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileChange}
          multiple
        />
        <Button
          variant="outline"
          size="icon"
          className="shrink-0"
          onClick={handleFileUpload}
        >
          <Upload className="size-4" />
        </Button>
        {onRefresh && (
          <Button
            variant="outline"
            size="icon"
            className="shrink-0"
            onClick={onRefresh}
          >
            <RefreshCw className="size-4" />
          </Button>
        )}
        <div className="flex-1">
          <Input
            placeholder="Type a message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full"
          />
        </div>
        <Button
          className="shrink-0"
          onClick={handleSendMessage}
          disabled={!inputValue.trim()}
        >
          <Send className="size-4" />
        </Button>
      </CardFooter>
    </Card>
  );
} 