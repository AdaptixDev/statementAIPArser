"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { ChatWindow } from "@/components/layout/chat-window";
import { SummaryCard } from "@/components/layout/summary-card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

export default function Home() {
  const [leftChatMessages, setLeftChatMessages] = useState([
    {
      id: "1",
      content: "Hello, how can I help you analyse financial statements or documents?",
      isUser: false,
    },
  ]);

  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [summaryData, setSummaryData] = useState<string | null>(null);

  const handleFileUpload = (file: File) => {
    console.log("File uploaded:", file.name);
    setUploadedFile(file);
    
    // Add a message to show the file was uploaded
    setLeftChatMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        content: `Uploaded file: ${file.name}`,
        isUser: true,
      }
    ]);
  };

  const handleAnalyzePDF = async () => {
    if (!uploadedFile) {
      setLeftChatMessages(prev => [
        ...prev,
        {
          id: Date.now().toString(),
          content: "Please upload a PDF file first.",
          isUser: false,
        }
      ]);
      return;
    }

    setIsProcessing(true);
    
    // Add a message to show processing has started
    setLeftChatMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        content: "Processing your PDF. This may take a few minutes...",
        isUser: false,
      }
    ]);

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await fetch('/api/process-pdf', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        // Use the actual summary data from the API response
        // The summary.txt file is already in JSON format, so we can use it directly
        setSummaryData(data.summary);
        
        // Add a success message to the chat (without the summary content)
        setLeftChatMessages(prev => [
          ...prev,
          {
            id: Date.now().toString(),
            content: "Analysis complete! Check the summary panel for details.",
            isUser: false,
          }
        ]);
      } else {
        // Show error message
        setLeftChatMessages(prev => [
          ...prev,
          {
            id: Date.now().toString(),
            content: `Error: ${data.error || 'Failed to process PDF'}`,
            isUser: false,
          }
        ]);
      }
    } catch (error) {
      console.error('Error processing PDF:', error);
      setLeftChatMessages(prev => [
        ...prev,
        {
          id: Date.now().toString(),
          content: `Error: ${error instanceof Error ? error.message : 'Failed to process PDF'}`,
          isUser: false,
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSendMessage = (message: string) => {
    const newMessage = {
      id: Date.now().toString(),
      content: message,
      isUser: true,
    };

    setLeftChatMessages(prev => [...prev, newMessage]);
  };

  return (
    <AppLayout>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[calc(100vh-160px)]">
        <div className="flex flex-col h-full">
          <ChatWindow 
            title="Statement Analysis" 
            messages={leftChatMessages}
            onSendMessage={handleSendMessage}
            onRefresh={() => setLeftChatMessages([leftChatMessages[0]])}
            onFileUpload={handleFileUpload}
          />
          <div className="mt-2">
            <Button 
              className="w-full"
              onClick={handleAnalyzePDF}
              disabled={isProcessing || !uploadedFile}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                'Analyze PDF'
              )}
            </Button>
          </div>
        </div>
        <SummaryCard 
          title="Statement Summary" 
          summary={summaryData}
        />
      </div>
    </AppLayout>
  );
}
