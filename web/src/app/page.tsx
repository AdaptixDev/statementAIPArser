"use client";

import { useState, useEffect } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { ChatWindow } from "@/components/layout/chat-window";
import { SummaryCard } from "@/components/layout/summary-card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

export default function Home() {
  // Define the message type
  interface ChatMessage {
    id: string;
    content: string;
    isUser: boolean;
    isProcessing?: boolean;
  }

  const [leftChatMessages, setLeftChatMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      content: "Hello, how can I help you analyse financial statements or documents?",
      isUser: false,
    },
  ]);

  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [summaryData, setSummaryData] = useState<string | null>(null);
  const [drivingLicenseData, setDrivingLicenseData] = useState<string | null>(null);

  const processingMessages = [
    "Extracting data from documents...",
    "Running advanced analysis algorithms...",
    "Identifying key financial patterns...",
    "Calculating financial metrics...",
    "Generating comprehensive summary...",
    "Validating document authenticity...",
    "Cross-referencing information...",
    "Applying machine learning models...",
  ];
  const [processingMessageInterval, setProcessingMessageInterval] = useState<NodeJS.Timeout | null>(null);

  // Function to detect document type and add appropriate message
  const detectAndNotifyDocumentType = (file: File) => {
    const fileName = file.name.toLowerCase();
    const fileType = file.type;
    
    let documentType = "Unknown document";
    
    if (fileName.endsWith('.pdf') && fileName.includes('statement')) {
      documentType = "Bank Statement";
    } else if (fileName.endsWith('.pdf')) {
      documentType = "PDF Document";
    } else if ((fileType.includes('image/') || fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || fileName.endsWith('.png')) 
              && (fileName.includes('licence') || fileName.includes('license') || fileName.includes('dl'))) {
      documentType = "Driving License";
    } else if (fileType.includes('image/') || fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || fileName.endsWith('.png')) {
      documentType = "Image Document";
    }
    
    // Add message to chat
    setLeftChatMessages(prev => [
      ...prev,
      {
        id: generateUniqueId(),
        content: `${documentType} detected: ${file.name}`,
        isUser: false,
      }
    ]);
    
    return documentType;
  };

  // Function to generate a unique ID
  const generateUniqueId = () => {
    return Date.now().toString() + '-' + Math.random().toString(36).substr(2, 9);
  };

  // Start the processing message updates
  const startProcessingMessages = () => {
    // Clear any existing interval
    if (processingMessageInterval) {
      clearInterval(processingMessageInterval);
    }
    
    // Add the first processing message
    const firstMessageId = generateUniqueId();
    setLeftChatMessages(prev => [
      ...prev,
      {
        id: firstMessageId,
        content: processingMessages[0],
        isUser: false,
        isProcessing: true,
      }
    ]);
    
    // Set up the interval to update the message
    const interval = setInterval(() => {
      // Update the last message with the new processing message
      setLeftChatMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        
        // Only update if it's a processing message (not a user message or other system message)
        if (lastMessage && lastMessage.id === firstMessageId) {
          // Get a random processing message
          const randomIndex = Math.floor(Math.random() * processingMessages.length);
          newMessages[newMessages.length - 1] = {
            ...lastMessage,
            content: processingMessages[randomIndex],
          };
        }
        
        return newMessages;
      });
    }, 5000); // Update every 5 seconds
    
    setProcessingMessageInterval(interval);
  };

  // Stop the processing messages
  const stopProcessingMessages = () => {
    if (processingMessageInterval) {
      clearInterval(processingMessageInterval);
      setProcessingMessageInterval(null);
      
      // Update the last message to remove the processing flag
      setLeftChatMessages(prev => {
        const newMessages = [...prev];
        if (newMessages.length > 0) {
          const lastMessage = newMessages[newMessages.length - 1];
          if (lastMessage.isProcessing) {
            newMessages[newMessages.length - 1] = {
              ...lastMessage,
              isProcessing: false,
            };
          }
        }
        return newMessages;
      });
    }
  };

  // Clean up the interval when the component unmounts
  useEffect(() => {
    return () => {
      if (processingMessageInterval) {
        clearInterval(processingMessageInterval);
      }
    };
  }, [processingMessageInterval]);

  const handleFileUpload = (file: File) => {
    console.log("File uploaded:", file.name);
    setUploadedFiles(prev => [...prev, file]);
    
    // Detect and notify document type
    detectAndNotifyDocumentType(file);
  };

  const handleMultipleFilesUpload = (files: File[]) => {
    console.log("Multiple files uploaded:", files.map(f => f.name).join(", "));
    setUploadedFiles(prev => [...prev, ...files]);
    
    // Detect and notify document types for each file
    const documentTypes = files.map(file => detectAndNotifyDocumentType(file));
    
    // Add a summary message if multiple documents
    if (files.length > 1) {
      setLeftChatMessages(prev => [
        ...prev,
        {
          id: generateUniqueId(),
          content: `${files.length} documents uploaded: ${documentTypes.join(", ")}`,
          isUser: false,
        }
      ]);
    }
  };

  const handleAnalyzeDocuments = async () => {
    if (uploadedFiles.length === 0) {
      setLeftChatMessages(prev => [
        ...prev,
        {
          id: generateUniqueId(),
          content: "Please upload at least one document first.",
          isUser: false,
        }
      ]);
      return;
    }

    setIsProcessing(true);
    
    // Start the processing messages
    startProcessingMessages();

    try {
      // Process each file based on its type
      for (const file of uploadedFiles) {
        const fileName = file.name.toLowerCase();
        const fileType = file.type;
        
        // Check if it's a PDF statement
        if (fileName.endsWith('.pdf') && fileName.includes('statement')) {
          await processStatementPDF(file);
        } 
        // Check if it's a driving license image
        else if ((fileType.includes('image/') || fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || fileName.endsWith('.png')) 
                && (fileName.includes('licence') || fileName.includes('license') || fileName.includes('dl'))) {
          await processDrivingLicense(file);
        }
        // Default to statement processing for PDFs
        else if (fileName.endsWith('.pdf')) {
          await processStatementPDF(file);
        }
        // Default to driving license processing for images
        else if (fileType.includes('image/') || fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || fileName.endsWith('.png')) {
          await processDrivingLicense(file);
        }
        else {
          // Unsupported file type
          setLeftChatMessages(prev => [
            ...prev,
            {
              id: generateUniqueId(),
              content: `Unsupported file type: ${file.name}. Please upload PDF statements or image files for driving licenses.`,
              isUser: false,
            }
          ]);
        }
      }
      
      // Stop the processing messages
      stopProcessingMessages();
      
      // Add a success message to the chat
      setLeftChatMessages(prev => [
        ...prev,
        {
          id: generateUniqueId(),
          content: "Analysis complete! Check the summary panel for details.",
          isUser: false,
        }
      ]);
      
    } catch (error) {
      console.error('Error processing documents:', error);
      
      // Stop the processing messages
      stopProcessingMessages();
      
      setLeftChatMessages(prev => [
        ...prev,
        {
          id: generateUniqueId(),
          content: `Error: ${error instanceof Error ? error.message : 'Failed to process documents'}`,
          isUser: false,
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const processStatementPDF = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/process-pdf', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    
    // Log the API response for debugging
    console.log("API Response:", data);
    console.log("Summary data from API:", data.summary);
    
    // Try to parse the summary data to see the actual values
    try {
      const parsedSummary = JSON.parse(data.summary);
      console.log("Parsed summary data:", parsedSummary);
      if (parsedSummary.summaryOfIncomeAndOutgoings) {
        console.log("Income data:", parsedSummary.summaryOfIncomeAndOutgoings.income);
        console.log("Outgoings data:", parsedSummary.summaryOfIncomeAndOutgoings.outgoings);
      }
    } catch (error) {
      console.error("Error parsing summary data:", error);
    }

    if (response.ok) {
      // Use the actual summary data from the API response
      setSummaryData(data.summary);
    } else {
      throw new Error(data.error || 'Failed to process PDF statement');
    }
  };

  const processDrivingLicense = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/process-driving-license', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (response.ok) {
      // Set the driving license data
      setDrivingLicenseData(JSON.stringify(data.result));
    } else {
      throw new Error(data.error || 'Failed to process driving license');
    }
  };

  const handleSendMessage = (message: string) => {
    // Add the user message to the chat
    setLeftChatMessages(prev => [
      ...prev,
      {
        id: generateUniqueId(),
        content: message,
        isUser: true,
      }
    ]);
  };

  return (
    <AppLayout>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[calc(100vh-160px)]">
        <div className="flex flex-col h-full">
          <ChatWindow 
            title="Statement Analysis" 
            messages={leftChatMessages}
            onSendMessage={handleSendMessage}
            onRefresh={() => {
              setLeftChatMessages([leftChatMessages[0]]);
              setUploadedFiles([]);
              setSummaryData(null);
              setDrivingLicenseData(null);
            }}
            onFileUpload={handleFileUpload}
            onMultipleFilesUpload={handleMultipleFilesUpload}
          />
          <div className="mt-2 space-y-2">
            <Button 
              className="w-full"
              onClick={handleAnalyzeDocuments}
              disabled={isProcessing || uploadedFiles.length === 0}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                'Analyse Documents'
              )}
            </Button>
          </div>
        </div>
        
        <SummaryCard 
          title="Document Summary" 
          summary={summaryData}
          drivingLicense={drivingLicenseData}
        />
      </div>
    </AppLayout>
  );
}
