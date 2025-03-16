"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp } from "lucide-react";

interface SummaryCardProps {
  title: string;
  summary: string | null;
  drivingLicense: string | null;
  passport: string | null;
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

// Define the structure of driving license data
interface DrivingLicenseData {
  surname: string;
  forename: string;
  address: string;
  dateOfBirth: string;
  expiryDate: string;
  licenceNumber: string;
  raw_response?: string;
}

// Define the structure of passport data
interface PassportData {
  surname: string;
  forename: string;
  address: string;
  dateOfBirth: string;
  expiryDate: string;
  passportNumber: string;
  raw_response?: string;
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
    <div className={`border rounded-lg overflow-hidden ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 md:p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <h3 className="text-sm md:text-base font-medium">{title}</h3>
        {isOpen ? (
          <ChevronUp className="size-4 md:size-5 text-gray-500" />
        ) : (
          <ChevronDown className="size-4 md:size-5 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="p-3 md:p-4 text-sm md:text-base">
          {children}
        </div>
      )}
    </div>
  );
};

// Parse the identification document data
const parseIdentificationDocument = (documentText: string): DrivingLicenseData | PassportData | null => {
  if (!documentText) return null;
  
  try {
    // Clean up the input string - remove any "```json" or "```" markers
    let cleanedText = documentText.trim();
    
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
    
    // Log the cleaned text for debugging
    console.log("Cleaned identification document text:", cleanedText);
    
    // Parse the JSON
    const parsedData = JSON.parse(cleanedText);
    
    // Log the parsed data for debugging
    console.log("Parsed identification document data:", parsedData);
    
    // Check if it's a passport or driving license
    if ('passportNumber' in parsedData) {
      console.log("Detected passport data");
    } else if ('licenceNumber' in parsedData) {
      console.log("Detected driving license data");
    } else {
      console.log("Unknown identification document type");
    }
    
    return parsedData;
  } catch (error) {
    console.error("Failed to parse identification document data:", error);
    return null;
  }
};

// Determine if the data is a passport or driving license
const isPassportData = (data: DrivingLicenseData | PassportData | Record<string, unknown>): data is PassportData => {
  return Boolean(data && typeof data === 'object' && 'passportNumber' in data && data.passportNumber);
};

const isDrivingLicenseData = (data: DrivingLicenseData | PassportData | Record<string, unknown>): data is DrivingLicenseData => {
  return Boolean(data && typeof data === 'object' && 'licenceNumber' in data && data.licenceNumber);
};

export function SummaryCard({ title, summary, drivingLicense, passport }: SummaryCardProps) {
  // Add a ref for the card content
  const cardContentRef = React.useRef<HTMLDivElement>(null);
  
  // Parse the summary data
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
      
      // Log the cleaned text
      console.log("Cleaned summary text:", cleanedText);
      
      // Parse the JSON
      const parsedData = JSON.parse(cleanedText);
      
      // Log the parsed data for debugging
      console.log("Parsed summary data:", parsedData);
      
      return parsedData;
    } catch (error) {
      console.error("Failed to parse summary data:", error);
      return null;
    }
  };
  
  // Parse the data
  const summaryData = summary ? parseSummaryData(summary) : null;
  const drivingLicenseDocument = drivingLicense ? parseIdentificationDocument(drivingLicense) : null;
  const passportDocument = passport ? parseIdentificationDocument(passport) : null;
  
  // Extract passport and driving license data if available
  const passportData = passportDocument && isPassportData(passportDocument) ? passportDocument : null;
  const drivingLicenseData = drivingLicenseDocument && isDrivingLicenseData(drivingLicenseDocument) ? drivingLicenseDocument : null;
  
  // Use effect for simplified scroll management
  React.useEffect(() => {
    if (cardContentRef.current) {
      let scrollTimeout: NodeJS.Timeout | null = null;
      
      const handleScroll = () => {
        if (!cardContentRef.current) return;
        
        if (scrollTimeout) {
          clearTimeout(scrollTimeout);
        }
        
        scrollTimeout = setTimeout(() => {
          // Reset scroll timeout
        }, 250);
      };
      
      cardContentRef.current.addEventListener('scroll', handleScroll);
      
      return () => {
        if (cardContentRef.current) {
          cardContentRef.current.removeEventListener('scroll', handleScroll);
        }
        if (scrollTimeout) {
          clearTimeout(scrollTimeout);
        }
      };
    }
  }, []);

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

  // Render income and outgoings section with formatted values
  const renderIncomeAndOutgoings = () => {
    if (!summaryData) return null;
    
    const { summaryOfIncomeAndOutgoings } = summaryData;
    
    // Log the raw income and outgoings data
    console.log("Raw income data from JSON:", JSON.stringify(summaryOfIncomeAndOutgoings.income));
    console.log("Raw outgoings data from JSON:", JSON.stringify(summaryOfIncomeAndOutgoings.outgoings));
    
    // Calculate totals directly from the data
    const totalIncome = Object.values(summaryOfIncomeAndOutgoings.income).reduce((sum, val) => sum + val, 0);
    const totalOutgoings = Object.values(summaryOfIncomeAndOutgoings.outgoings).reduce((sum, val) => sum + val, 0);
    const netBalance = totalIncome - totalOutgoings;
    
    // Log the calculated totals
    console.log("Total income calculated:", totalIncome);
    console.log("Total outgoings calculated:", totalOutgoings);
    
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
            <span className={netBalance >= 0 ? "text-green-700" : "text-red-700"}>
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

  // Render driving license information
  const renderDrivingLicenseDocument = () => {
    if (!drivingLicenseData) return null;
    
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
        <h2 className="text-xl font-bold mb-3 text-blue-800">Driving License Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <p className="font-semibold">Surname</p>
            <p>{drivingLicenseData.surname}</p>
          </div>
          <div>
            <p className="font-semibold">Forename</p>
            <p>{drivingLicenseData.forename}</p>
          </div>
          <div>
            <p className="font-semibold">Address</p>
            <p>{drivingLicenseData.address || "Not available"}</p>
          </div>
          <div>
            <p className="font-semibold">Date of Birth</p>
            <p>{drivingLicenseData.dateOfBirth}</p>
          </div>
          <div>
            <p className="font-semibold">Expiry Date</p>
            <p>{drivingLicenseData.expiryDate}</p>
          </div>
          <div>
            <p className="font-semibold">License Number</p>
            <p>{drivingLicenseData.licenceNumber}</p>
          </div>
        </div>
      </div>
    );
  };
  
  // Render passport information
  const renderPassportDocument = () => {
    if (!passportData) return null;
    
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
        <h2 className="text-xl font-bold mb-3 text-blue-800">Passport Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <p className="font-semibold">Surname</p>
            <p>{passportData.surname}</p>
          </div>
          <div>
            <p className="font-semibold">Forename</p>
            <p>{passportData.forename}</p>
          </div>
          <div>
            <p className="font-semibold">Address</p>
            <p>{passportData.address || "Not available"}</p>
          </div>
          <div>
            <p className="font-semibold">Date of Birth</p>
            <p>{passportData.dateOfBirth}</p>
          </div>
          <div>
            <p className="font-semibold">Expiry Date</p>
            <p>{passportData.expiryDate}</p>
          </div>
          <div>
            <p className="font-semibold">Passport Number</p>
            <p>{passportData.passportNumber}</p>
          </div>
        </div>
      </div>
    );
  };
  
  // Render identification documents section
  const renderIdentificationDocuments = () => {
    if (!drivingLicenseData && !passportData) return null;
    
    return (
      <>
        {passportData && renderPassportDocument()}
        {drivingLicenseData && renderDrivingLicenseDocument()}
      </>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader className="px-4 py-3 border-b">
        <CardTitle className="text-lg font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-4 space-y-4">
        {summaryData && (
          <>
            <CollapsibleSection title="Personal Information" defaultOpen>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                {renderPersonalInfo()}
              </div>
            </CollapsibleSection>

            <CollapsibleSection title="Income & Outgoings">
              <div className="space-y-4">
                {renderIncomeAndOutgoings()}
              </div>
            </CollapsibleSection>

            <CollapsibleSection title="Financial Health Commentary">
              <div className="space-y-3">
                {renderFinancialHealthCommentary()}
              </div>
            </CollapsibleSection>

            <CollapsibleSection title="Potential Red Flags">
              <div className="space-y-2">
                {renderRedFlags()}
              </div>
            </CollapsibleSection>

            <CollapsibleSection title="Recommendations">
              <div className="space-y-2">
                {renderRecommendations()}
              </div>
            </CollapsibleSection>
          </>
        )}

        {(drivingLicense || passport) && (
          <CollapsibleSection title="Identification Documents">
            <div className="space-y-4">
              {renderIdentificationDocuments()}
            </div>
          </CollapsibleSection>
        )}

        {!summaryData && !drivingLicense && !passport && (
          <div className="flex items-center justify-center h-32">
            <p className="text-gray-500">No data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 