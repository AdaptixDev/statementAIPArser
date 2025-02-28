import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';

const execPromise = promisify(exec);

// Temporary directory for storing uploaded PDFs
const TEMP_DIR = path.join(process.cwd(), 'temp');
// Output directory for processing results
const OUTPUT_DIR = path.join(process.cwd(), 'output');
// Backend output directory for raw Gemini responses
const BACKEND_OUTPUT_DIR = path.join(process.cwd(), '..', 'backend', 'output');

// Ensure temp and output directories exist
if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true });
}
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}
if (!fs.existsSync(BACKEND_OUTPUT_DIR)) {
  fs.mkdirSync(BACKEND_OUTPUT_DIR, { recursive: true });
}

// Helper function to clean JSON string from markdown code blocks
function cleanJsonString(jsonString: string): string {
  let cleaned = jsonString.trim();
  
  // Remove markdown code block markers if present
  if (cleaned.startsWith("```json")) {
    cleaned = cleaned.substring(7);
  } else if (cleaned.startsWith("```")) {
    cleaned = cleaned.substring(3);
  }
  
  if (cleaned.endsWith("```")) {
    cleaned = cleaned.substring(0, cleaned.length - 3);
  }
  
  // Trim again after removing markers
  cleaned = cleaned.trim();
  
  return cleaned;
}

export async function POST(request: NextRequest) {
  try {
    // Get the form data from the request
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    // Check if the file is a PDF
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return NextResponse.json({ error: 'Only PDF files are supported' }, { status: 400 });
    }

    // Create a unique filename to avoid collisions
    const timestamp = Date.now();
    const filename = `${timestamp}_${file.name}`;
    const filePath = path.join(TEMP_DIR, filename);

    // Write the file to disk
    const buffer = Buffer.from(await file.arrayBuffer());
    fs.writeFileSync(filePath, buffer);

    // Create a unique output directory for this processing job
    const jobOutputDir = path.join(OUTPUT_DIR, `job_${timestamp}`);
    fs.mkdirSync(jobOutputDir, { recursive: true });

    // Get the absolute path to the backend script
    const backendScriptPath = path.join(process.cwd(), '..', 'backend', 'run_gemini_processor.py');

    // Execute the Python script
    const { stdout, stderr } = await execPromise(
      `python "${backendScriptPath}" --pdf "${filePath}" --output "${jobOutputDir}"`
    );

    console.log('Python script output:', stdout);
    if (stderr) {
      console.error('Python script error:', stderr);
    }

    // Read the summary file
    const summaryPath = path.join(jobOutputDir, 'summary.txt');
    let summary = '';
    let cleanedSummary = '';
    
    if (fs.existsSync(summaryPath)) {
      summary = fs.readFileSync(summaryPath, 'utf-8');
      console.log('Raw summary file content:', summary);
      
      // Save the raw Gemini response to the backend output directory
      const rawResponsePath = path.join(BACKEND_OUTPUT_DIR, `raw_gemini_response_${timestamp}.txt`);
      fs.writeFileSync(rawResponsePath, summary);
      console.log(`Raw Gemini response saved to: ${rawResponsePath}`);
      
      // Clean the JSON string by removing markdown code block markers
      cleanedSummary = cleanJsonString(summary);
      console.log('Cleaned summary content:', cleanedSummary);
      
      // Try to parse the JSON to verify it's valid
      try {
        const parsedSummary = JSON.parse(cleanedSummary);
        console.log('Parsed summary income:', parsedSummary.summaryOfIncomeAndOutgoings?.income);
        console.log('Parsed summary outgoings:', parsedSummary.summaryOfIncomeAndOutgoings?.outgoings);
        
        // Replace the original summary with the cleaned version
        summary = cleanedSummary;
      } catch (parseError) {
        console.error('Error parsing summary JSON:', parseError);
      }
    } else {
      summary = 'Summary file not found. Processing may have failed.';
    }

    // Clean up the temporary file
    fs.unlinkSync(filePath);

    return NextResponse.json({ 
      success: true, 
      summary,
      message: 'PDF processed successfully' 
    });
  } catch (error) {
    console.error('Error processing PDF:', error);
    return NextResponse.json({ 
      error: 'Failed to process PDF', 
      details: error instanceof Error ? error.message : String(error) 
    }, { status: 500 });
  }
} 