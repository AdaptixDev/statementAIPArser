"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp } from "lucide-react";

interface SummaryCardProps {
  title: string;
  summary: string | null;
}

// Define the structure of our summary data
interface SummaryData {
  personalInformation: {
    name: string;
    address: string;
    accountNumber: string;
    sortCode: string;
    statementStartingBalance: number;
    statementFinishingBalance: number;
  };
  summaryOfIncomeAndOutgoings: {
    income: Record<string, number>;
    outgoings: Record<string, number>;
  };
  generalSummaryAndFinancialHealthCommentary: Record<string, string>;
  potentialRedFlagsAndConcerns: string[];
  recommendations: string[];
}

// Collapsible section component
interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({ 
  title, 
  children, 
  defaultOpen = false,
  className = ""
}) => {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  return (
    <div className={`border rounded-lg overflow-hidden mb-4 ${className}`}>
      <button
        className="w-full flex justify-between items-center p-3 bg-gray-100 hover:bg-gray-200 transition-colors text-left"
        onClick={() => setIsOpen(!isOpen)}
      >
        <h2 className="text-lg font-semibold">{title}</h2>
        {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </button>
      {isOpen && (
        <div className="p-4">
          {children}
        </div>
      )}
    </div>
  );
};

export function SummaryCard({ title, summary }: SummaryCardProps) {
  // Parse the JSON data from the summary text
  const parseSummaryData = (summaryText: string): SummaryData | null => {
    if (!summaryText) return null;
    
    try {
      // Clean up the input string - remove any "```json" or "```" markers
      let cleanedText = summaryText.trim();
      
      // Remove markdown code block markers if present
      if (cleanedText.startsWith("```json")) {
        cleanedText = cleanedText.substring(7);
      }
      if (cleanedText.startsWith("```")) {
        cleanedText = cleanedText.substring(3);
      }
      if (cleanedText.endsWith("```")) {
        cleanedText = cleanedText.substring(0, cleanedText.length - 3);
      }
      
      // Trim again after removing markers
      cleanedText = cleanedText.trim();
      
      // Parse the JSON
      return JSON.parse(cleanedText);
    } catch (error) {
      console.error("Failed to parse summary data:", error);
      return null;
    }
  };

  const summaryData = summary ? parseSummaryData(summary) : null;

  // Format currency values
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
    }).format(value);
  };

  // Format field names to be more readable
  const formatFieldName = (name: string): string => {
    // Convert camelCase to Title Case with spaces
    return name
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (str) => str.toUpperCase());
  };

  // Render personal information section
  const renderPersonalInfo = () => {
    if (!summaryData) return null;
    
    const { personalInformation } = summaryData;
    
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
        <h2 className="text-xl font-bold mb-3 text-blue-800">Personal Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <p className="font-semibold">Name</p>
            <p>{personalInformation.name}</p>
          </div>
          <div>
            <p className="font-semibold">Address</p>
            <p>{personalInformation.address}</p>
          </div>
          <div>
            <p className="font-semibold">Account Number</p>
            <p>{personalInformation.accountNumber}</p>
          </div>
          <div>
            <p className="font-semibold">Sort Code</p>
            <p>{personalInformation.sortCode}</p>
          </div>
          <div>
            <p className="font-semibold">Starting Balance</p>
            <p className={personalInformation.statementStartingBalance < 0 ? "text-red-600" : "text-green-600"}>
              {formatCurrency(personalInformation.statementStartingBalance)}
            </p>
          </div>
          <div>
            <p className="font-semibold">Finishing Balance</p>
            <p className={personalInformation.statementFinishingBalance < 0 ? "text-red-600" : "text-green-600"}>
              {formatCurrency(personalInformation.statementFinishingBalance)}
            </p>
          </div>
        </div>
      </div>
    );
  };

  // Render income and outgoings section
  const renderIncomeAndOutgoings = () => {
    if (!summaryData) return null;
    
    const { summaryOfIncomeAndOutgoings } = summaryData;
    const totalIncome = Object.values(summaryOfIncomeAndOutgoings.income).reduce((sum, val) => sum + val, 0);
    const totalOutgoings = Object.values(summaryOfIncomeAndOutgoings.outgoings).reduce((sum, val) => sum + val, 0);
    const netBalance = totalIncome - totalOutgoings;
    
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
        <h2 className="text-xl font-bold mb-3 text-blue-800">Income & Outgoings Summary</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-2 text-green-700">Income</h3>
            <div className="space-y-1">
              {Object.entries(summaryOfIncomeAndOutgoings.income).map(([category, amount]) => (
                <div key={`income-${category}`} className="flex justify-between">
                  <span>{category}</span>
                  <span className="font-medium">{formatCurrency(amount)}</span>
                </div>
              ))}
              <div className="flex justify-between border-t pt-1 font-bold">
                <span>Total Income</span>
                <span className="text-green-700">{formatCurrency(totalIncome)}</span>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-2 text-red-700">Outgoings</h3>
            <div className="space-y-1">
              {Object.entries(summaryOfIncomeAndOutgoings.outgoings).map(([category, amount]) => (
                <div key={`outgoing-${category}`} className="flex justify-between">
                  <span>{category}</span>
                  <span className="font-medium">{formatCurrency(amount)}</span>
                </div>
              ))}
              <div className="flex justify-between border-t pt-1 font-bold">
                <span>Total Outgoings</span>
                <span className="text-red-700">{formatCurrency(totalOutgoings)}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-4 pt-2 border-t">
          <div className="flex justify-between font-bold text-lg">
            <span>Net Balance</span>
            <span className={netBalance < 0 ? "text-red-600" : "text-green-600"}>
              {formatCurrency(netBalance)}
            </span>
          </div>
        </div>
      </div>
    );
  };

  // Render financial health commentary
  const renderFinancialHealthCommentary = () => {
    if (!summaryData) return null;
    
    const { generalSummaryAndFinancialHealthCommentary } = summaryData;
    
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
        <h2 className="text-xl font-bold mb-3 text-blue-800">Financial Health Commentary</h2>
        <div className="space-y-3">
          {Object.entries(generalSummaryAndFinancialHealthCommentary).map(([key, value]) => (
            <div key={key}>
              <h3 className="font-semibold">{formatFieldName(key)}</h3>
              <p>{value}</p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render red flags section
  const renderRedFlags = () => {
    if (!summaryData || !summaryData.potentialRedFlagsAndConcerns.length) return null;
    
    return (
      <div className="bg-red-50 rounded-lg p-4 shadow-sm mb-4 border border-red-200">
        <h2 className="text-xl font-bold mb-3 text-red-800">Potential Red Flags & Concerns</h2>
        <ul className="list-disc pl-5 space-y-1">
          {summaryData.potentialRedFlagsAndConcerns.map((flag, index) => (
            <li key={index}>{flag}</li>
          ))}
        </ul>
      </div>
    );
  };

  // Render recommendations section
  const renderRecommendations = () => {
    if (!summaryData || !summaryData.recommendations.length) return null;
    
    return (
      <div className="bg-green-50 rounded-lg p-4 shadow-sm mb-4 border border-green-200">
        <h2 className="text-xl font-bold mb-3 text-green-800">Recommendations</h2>
        <ul className="list-disc pl-5 space-y-1">
          {summaryData.recommendations.map((recommendation, index) => (
            <li key={index}>{recommendation}</li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="bg-gray-100 border-b">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-4 bg-gray-50">
        {!summary ? (
          <div className="space-y-4">
            <CollapsibleSection title="Statement Summary" defaultOpen={false}>
              <div className="flex items-center justify-center py-4">
                <p className="text-gray-500 text-center">Upload and analyze a statement to see the summary</p>
              </div>
            </CollapsibleSection>
            
            <CollapsibleSection 
              title="Identification Documents" 
              defaultOpen={false}
              className="bg-white"
            >
              <div className="py-4 text-center text-gray-500">
                <p>No identification documents available.</p>
              </div>
            </CollapsibleSection>
            
            <CollapsibleSection 
              title="Supporting Documents" 
              defaultOpen={false}
              className="bg-white"
            >
              <div className="py-4 text-center text-gray-500">
                <p>No supporting documents available.</p>
              </div>
            </CollapsibleSection>
          </div>
        ) : !summaryData ? (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800">Unable to parse the summary data. Please ensure it&apos;s in the correct format.</p>
            <pre className="mt-2 text-xs overflow-auto max-h-40 bg-gray-100 p-2 rounded">
              {summary}
            </pre>
          </div>
        ) : (
          <div className="space-y-4">
            <CollapsibleSection title="Statement Summary" defaultOpen={false}>
              <div className="space-y-4">
                {renderPersonalInfo()}
                {renderIncomeAndOutgoings()}
                {renderFinancialHealthCommentary()}
                {renderRedFlags()}
                {renderRecommendations()}
              </div>
            </CollapsibleSection>
            
            <CollapsibleSection 
              title="Identification Documents" 
              defaultOpen={false}
              className="bg-white"
            >
              <div className="py-4 text-center text-gray-500">
                <p>No identification documents available.</p>
              </div>
            </CollapsibleSection>
            
            <CollapsibleSection 
              title="Supporting Documents" 
              defaultOpen={false}
              className="bg-white"
            >
              <div className="py-4 text-center text-gray-500">
                <p>No supporting documents available.</p>
              </div>
            </CollapsibleSection>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 