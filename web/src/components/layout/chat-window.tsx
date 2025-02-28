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
    <Card className="flex flex-col h-full">
      <CardHeader className="bg-gray-100 border-b">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent 
        className="flex-1 overflow-y-auto p-4 space-y-4 text-sm" 
        ref={messagesContainerRef}
        onScroll={handleScroll}
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500 text-center">No messages yet</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.isUser
                    ? "bg-gray-800 text-white"
                    : message.isProcessing
                      ? "processing-message text-gray-900"
                      : "bg-gray-100 text-gray-900"
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </CardContent>
      <CardFooter className="border-t p-3 gap-2 flex flex-col">
        <div className="flex w-full gap-2">
          <Input
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 text-sm"
          />
          <Button 
            variant="outline"
            onClick={onRefresh}
          >
            <RefreshCw className="size-4" />
          </Button>
        </div>
        <div className="flex gap-2 w-full">
          {title === "Statement Analysis" && (
            <>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png"
                multiple
              />
              <Button 
                variant="outline"
                onClick={handleFileUpload}
                className="flex-1 text-sm"
              >
                <Upload className="size-4 mr-2" />
                Upload
              </Button>
            </>
          )}
          <Button 
            className="flex-1 text-sm"
            onClick={handleSendMessage}
          >
            <Send className="size-4 mr-2" />
            Send
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
} 