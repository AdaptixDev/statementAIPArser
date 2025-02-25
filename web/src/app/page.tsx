"use client";

import { AppLayout } from "@/components/layout/app-layout";
import { ChatWindow } from "@/components/layout/chat-window";

export default function Home() {
  // Mock data for demonstration
  const leftChatMessages = [
    {
      id: "1",
      content: "Hello! How can I help you analyse your financial statements?",
      isUser: false,
    },
  ];

  const rightChatMessages = [
    {
      id: "1",
      content: "Welcome to the personal finance assistant. I can help you understand your spending patterns.",
      isUser: false,
    },
    {
      id: "2",
      content: "Can you categorize my expenses?",
      isUser: true,
    },
    {
      id: "3",
      content: "Of course! I'll analyze your transactions and group them into categories like groceries, utilities, entertainment, etc.",
      isUser: false,
    },
  ];

  const handleFileUpload = (file: File) => {
    console.log("File uploaded:", file.name);
    // Here you would typically process the file or send it to an API
  };

  return (
    <AppLayout>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[calc(100vh-160px)]">
        <ChatWindow 
          title="Statement Analysis" 
          messages={leftChatMessages}
          onSendMessage={(message) => console.log("Send message in left chat:", message)}
          onRefresh={() => console.log("Refresh left chat")}
          onFileUpload={handleFileUpload}
        />
        <ChatWindow 
          title="Personal Finance Assistant" 
          messages={rightChatMessages}
          onSendMessage={(message) => console.log("Send message in right chat:", message)}
          onRefresh={() => console.log("Refresh right chat")}
        />
      </div>
    </AppLayout>
  );
}
