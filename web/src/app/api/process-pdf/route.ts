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

// Ensure temp and output directories exist
if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true });
}
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
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
    
    if (fs.existsSync(summaryPath)) {
      summary = fs.readFileSync(summaryPath, 'utf-8');
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