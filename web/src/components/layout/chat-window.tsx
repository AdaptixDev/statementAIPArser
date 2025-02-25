"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Send, RefreshCw, Upload } from "lucide-react";
import { Input } from "../../components/ui/input";

interface ChatWindowProps {
  title: string;
  messages: Array<{
    id: string;
    content: string;
    isUser: boolean;
  }>;
  onSendMessage?: (message: string) => void;
  onRefresh?: () => void;
  onFileUpload?: (file: File) => void;
}

export function ChatWindow({ title, messages, onSendMessage, onRefresh, onFileUpload }: ChatWindowProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [inputValue, setInputValue] = React.useState("");

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && onFileUpload) {
      onFileUpload(file);
    }
  };

  const handleSendMessage = () => {
    if (inputValue.trim() && onSendMessage) {
      onSendMessage(inputValue);
      setInputValue("");
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
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
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
            className="flex-1"
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
                accept=".pdf,.csv,.xlsx,.xls"
              />
              <Button 
                variant="outline"
                onClick={handleFileUpload}
                className="flex-1"
              >
                <Upload className="size-4 mr-2" />
                Upload
              </Button>
            </>
          )}
          <Button 
            className="flex-1"
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