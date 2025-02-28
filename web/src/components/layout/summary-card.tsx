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
  
  // Use effect to prevent auto-scrolling
  React.useEffect(() => {
    let isManualScroll = false;
    let scrollTimeout: NodeJS.Timeout | null = null;
    
    // Disable auto-scrolling behavior
    const handleScroll = () => {
      if (!cardContentRef.current) return;
      
      // If this is a manual scroll, mark it
      isManualScroll = true;
      
      // Clear any existing timeout
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }
      
      // Set a timeout to reset the manual scroll flag
      scrollTimeout = setTimeout(() => {
        isManualScroll = false;
      }, 100);
    };
    
    // Handle any automatic scrolling that might occur
    const checkForAutoScroll = () => {
      if (!cardContentRef.current || isManualScroll) return;
      
      // If we're not at the top and we didn't manually scroll, it's likely an auto-scroll
      if (cardContentRef.current.scrollTop > 0) {
        cardContentRef.current.scrollTop = 0;
      }
    };
    
    // Set up an interval to check for auto-scrolling
    const intervalId = setInterval(checkForAutoScroll, 100);
    
    // Add event listener to the card content
    const currentRef = cardContentRef.current;
    if (currentRef) {
      currentRef.addEventListener('scroll', handleScroll);
    }
    
    // Clean up
    return () => {
      if (currentRef) {
        currentRef.removeEventListener('scroll', handleScroll);
      }
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }
      clearInterval(intervalId);
    };
  }, []);

  // Use effect to maintain scroll position
  React.useEffect(() => {
    // Create a MutationObserver to watch for changes in the card content
    if (cardContentRef.current) {
      let lastScrollTop = 0;
      
      // Function to store the current scroll position
      const storeScrollPosition = () => {
        if (cardContentRef.current) {
          lastScrollTop = cardContentRef.current.scrollTop;
        }
      };
      
      // Function to restore the scroll position
      const restoreScrollPosition = () => {
        if (cardContentRef.current && cardContentRef.current.scrollTop !== lastScrollTop) {
          cardContentRef.current.scrollTop = lastScrollTop;
        }
      };
      
      // Create a MutationObserver to watch for changes
      const observer = new MutationObserver(() => {
        // Restore scroll position after DOM changes
        restoreScrollPosition();
      });
      
      // Start observing the card content for changes
      observer.observe(cardContentRef.current, { 
        childList: true, 
        subtree: true,
        attributes: true,
        characterData: true
      });
      
      // Add event listener to store scroll position before changes
      cardContentRef.current.addEventListener('scroll', storeScrollPosition);
      
      // Clean up
      return () => {
        observer.disconnect();
        if (cardContentRef.current) {
          cardContentRef.current.removeEventListener('scroll', storeScrollPosition);
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
    <Card className="flex flex-col h-full">
      <CardHeader className="bg-gray-100 border-b">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent ref={cardContentRef} className="flex-1 overflow-auto p-4 bg-gray-50 text-sm">
        {!summary && !drivingLicense && !passport ? (
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
        ) : (
          <div className="space-y-4">
            <CollapsibleSection 
              title="Statement Summary" 
              defaultOpen={summary !== null}
            >
              {summary ? (
                summaryData ? (
                  <div className="space-y-4">
                    {renderPersonalInfo()}
                    {renderIncomeAndOutgoings()}
                    {renderFinancialHealthCommentary()}
                    {renderRedFlags()}
                    {renderRecommendations()}
                  </div>
                ) : (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-yellow-800">Unable to parse the statement data. Please ensure it&apos;s in the correct format.</p>
                    <pre className="mt-2 text-xs overflow-auto max-h-40 bg-gray-100 p-2 rounded">
                      {summary}
                    </pre>
                  </div>
                )
              ) : (
                <div className="flex items-center justify-center py-4">
                  <p className="text-gray-500 text-center">Upload and analyze a statement to see the summary</p>
                </div>
              )}
            </CollapsibleSection>
            
            <CollapsibleSection 
              title="Identification Documents" 
              defaultOpen={drivingLicense !== null || passport !== null}
              className="bg-white"
            >
              {drivingLicense || passport ? (
                renderIdentificationDocuments()
              ) : (
                <div className="py-4 text-center text-gray-500">
                  <p>No identification documents available.</p>
                </div>
              )}
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