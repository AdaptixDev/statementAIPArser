"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { ChatWindow } from "@/components/layout/chat-window";
import { SummaryCard } from "@/components/layout/summary-card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

// Sample JSON structure for testing - this matches the actual summary.txt data
const sampleJsonData = {
  personalInformation: {
    name: "MR CHRISTOPHER J BYRON",
    address: "89 FLIXTON ROAD, URMSTON, MANCHESTER, M41 5AN",
    accountNumber: "10212003",
    sortCode: "16-33-22",
    statementStartingBalance: 64.97,
    statementFinishingBalance: -814.79
  },
  summaryOfIncomeAndOutgoings: {
    income: {
      "Bank Transfer": 8749.77,
      "Gambling": 668.85,
      "Unknown": 681.64
    },
    outgoings: {
      "Cash Withdrawal": 285.57,
      "Gambling": 863.22,
      "Non-Essential Household": 241.83,
      "Non -Essential Entertainment": 1476.94,
      "Bank Transfer": 1106.66,
      "Essential Household": 114.0,
      "Unknown": 4931.96
    }
  },
  generalSummaryAndFinancialHealthCommentary: {
    overallBalance: "The account balance has decreased by £879.76 during the statement period (from £64.97 to -£814.79).",
    inconsistentCategorization: "There are a lot of transactions labelled as 'Unknown.' More specific categorization is needed for proper budgeting and analysis.",
    essentialHouseholdSpending: "A small amount is spent on essential household bills.",
    transfers: "Frequent transfers to and from 'BYRON C' and 'BYRON CJ' suggest money moving between accounts without clear purposes.",
    paymentsToIndividuals: "Payments from Kevin Byron and Julia Byron.",
    gamblingTransactions: "Numerous transactions related to gambling (PADDY POWER, POKERSTARS, BETMGM, BETFAIR, NATIONAL LOTTERY) indicate regular gambling activity.",
    nonEssentialEntertainment: "Significant spending on non-essential entertainment, including restaurants, bars, and Uber trips.",
    negativeBalance: "The account has a negative balance at the end of the statement period, indicating an overdraft or potential financial strain."
  },
  potentialRedFlagsAndConcerns: [
    "High 'Unknown' Category Spending: Indicates lack of tracking and control over finances.",
    "Frequent Gambling Transactions: Suggests potential gambling addiction and financial risks.",
    "Significant Non-Essential Spending: High spending on entertainment and non-essential items may be unsustainable.",
    "Negative Balance: Overspending and reliance on overdraft facilities may lead to debt accumulation.",
    "Dependence on Transfers: Income includes transfers from various sources, suggesting potential financial instability."
  ],
  recommendations: [
    "Categorize Transactions: Categorize all 'Unknown' items to see where money is truly going.",
    "Budgeting: Create a detailed budget to manage income and expenses.",
    "Investigate Transfers: Understand the purpose of frequent transfers to 'BYRON C' and 'BYRON CJ'.",
    "Seek Help for Gambling: If gambling is causing financial or personal issues, seek help from a gambling support organization.",
    "Reduce Non-Essential Spending: Identify areas where non-essential spending can be reduced to improve financial stability.",
    "Avoid Overdraft: Take steps to avoid overdraft charges by managing expenses and ensuring sufficient funds in the account.",
    "Seek Financial Advice: If financial management is challenging, consult a professional for personalized advice."
  ]
};

export default function Home() {
  const [leftChatMessages, setLeftChatMessages] = useState([
    {
      id: "1",
      content: "Hello! How can I help you analyse your financial statements?",
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

  // For demo/testing purposes - use sample data
  const handleUseSampleData = () => {
    setSummaryData(JSON.stringify(sampleJsonData));
    
    setLeftChatMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        content: "Using sample data for demonstration.",
        isUser: false,
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
          <div className="mt-2 flex gap-2">
            <Button 
              className="flex-1"
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
            <Button 
              variant="outline"
              onClick={handleUseSampleData}
              disabled={isProcessing}
            >
              Use Sample Data
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
