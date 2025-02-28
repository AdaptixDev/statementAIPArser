import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';

const execPromise = promisify(exec);

// Temporary directory for storing uploaded images
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

    // Check if the file is an image
    const fileType = file.type;
    const fileName = file.name.toLowerCase();
    const isImage = fileType.startsWith('image/') || 
                    fileName.endsWith('.jpg') || 
                    fileName.endsWith('.jpeg') || 
                    fileName.endsWith('.png');

    if (!isImage) {
      return NextResponse.json({ error: 'Only image files are supported for passport processing' }, { status: 400 });
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
    const backendScriptPath = path.join(process.cwd(), '..', 'backend', 'parse_passport.py');

    // Execute the Python script
    const { stdout, stderr } = await execPromise(
      `python "${backendScriptPath}" --image "${filePath}" --output "${path.join(jobOutputDir, 'passport_data.json')}"`
    );

    console.log('Python script output:', stdout);
    if (stderr) {
      console.error('Python script error:', stderr);
    }

    // Read the result file
    const resultPath = path.join(jobOutputDir, 'passport_data.json');
    let result = null;
    
    if (fs.existsSync(resultPath)) {
      const resultData = fs.readFileSync(resultPath, 'utf-8');
      console.log('Raw passport data:', resultData);
      
      try {
        // Extract the first JSON object from the file
        const jsonStart = resultData.indexOf('{');
        const jsonEnd = resultData.indexOf('}') + 1;
        
        if (jsonStart >= 0 && jsonEnd > jsonStart) {
          const jsonContent = resultData.substring(jsonStart, jsonEnd);
          console.log('Extracted JSON content:', jsonContent);
          result = JSON.parse(jsonContent);
          console.log('Parsed passport data:', result);
        } else {
          // Try parsing the entire file
          result = JSON.parse(resultData);
        }
        
        // Ensure the result has the required fields for a passport
        if (!result.passportNumber) {
          console.warn('Passport data missing passport number:', result);
        }
      } catch (error) {
        console.error('Error parsing passport data:', error);
        return NextResponse.json({ 
          error: 'Failed to parse passport data', 
          details: error instanceof Error ? error.message : String(error) 
        }, { status: 500 });
      }
    } else {
      return NextResponse.json({ 
        error: 'Failed to process passport image. Result file not found.' 
      }, { status: 500 });
    }

    // Clean up the temporary file
    fs.unlinkSync(filePath);

    return NextResponse.json({ 
      success: true, 
      result,
      message: 'Passport image processed successfully' 
    });
  } catch (error) {
    console.error('Error processing passport image:', error);
    return NextResponse.json({ 
      error: 'Failed to process passport image', 
      details: error instanceof Error ? error.message : String(error) 
    }, { status: 500 });
  }
} 