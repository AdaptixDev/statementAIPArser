import os
import logging
from typing import List
from pdf2image import convert_from_path
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PDFConverter:
    @staticmethod
    def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 300) -> tuple[str, List[str]]:
        """
        Convert PDF file to high quality images.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the images
            dpi: Resolution for the output images (default: 300)

        Returns:
            Tuple containing (front_page_image_path, list_of_all_image_paths)
        """
        logging.info(f"Starting PDF conversion for: {pdf_path}")
        if not os.path.exists(output_dir):
            logging.info(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)

        # Explicit poppler path for Windows - updated with correct library/bin path
        poppler_path = r"C:\Users\cbyro\OneDrive\cursorWorkspace\statementAIParser\poppler\Release-24.08.0-0\poppler-24.08.0\library\bin"
        
        # Check if poppler path exists
        if not os.path.exists(poppler_path):
            raise ValueError(f"Poppler path does not exist: {poppler_path}")
        
        logging.info(f"Using poppler path: {poppler_path}")
        logging.info("Converting PDF to images...")
        
        try:
            # Convert PDF to images with enhanced quality
            images = convert_from_path(
                pdf_path,
                poppler_path=poppler_path,  # Use explicit poppler path
                dpi=600,                    # Increased DPI for better resolution
                thread_count=2,             # Use multiple threads for faster processing
                fmt="jpeg"                  # Explicitly set format
            )
            logging.info(f"Successfully converted PDF to {len(images)} images")

            # Save images with maximum quality and highlight the front page
            image_paths = []
            for i, image in enumerate(images):
                # Highlight the front page by using '_front' in the filename
                if i == 0:
                    image_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_front.jpg"
                else:
                    image_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{i+1}.jpg"
                image_path = os.path.join(output_dir, image_filename)
                logging.info(f"Saving image {i+1} to: {image_path}")
                image.save(image_path, "JPEG", quality=100, optimize=False)
                image_paths.append(image_path)

            logging.info("PDF conversion completed successfully")
            return (image_paths[0], image_paths) if image_paths else (None, [])
            
        except Exception as e:
            logging.error(f"Error during PDF conversion: {str(e)}")
            if not os.path.exists(pdf_path):
                logging.error(f"PDF file does not exist: {pdf_path}")
            elif not os.access(pdf_path, os.R_OK):
                logging.error(f"PDF file is not readable: {pdf_path}")
            raise