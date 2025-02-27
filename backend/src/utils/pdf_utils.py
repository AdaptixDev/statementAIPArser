"""Utilities for PDF processing and conversion."""

import os
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Union
from pdf2image import convert_from_path
from PIL import Image
from io import BytesIO

# Import the settings so we can check our storage toggle
from backend.src.config.settings import Settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# We allow the return type to be either a list of file paths (str) or a list of tuples (pseudo_filename, image_bytes)
ImageData = Union[str, Tuple[str, bytes]]

class PDFConverter:
    @staticmethod
    def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 600) -> Tuple[ImageData, List[ImageData]]:
        """
        Convert PDF file to high quality images without any contrast enhancement.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the images (if file storage is enabled)
            dpi: Resolution for the output images (default: 600)

        Returns:
            Tuple containing (front_page, list_of_all_image_data)

            When file storage is enabled: image data is a file path (str)
            When file storage is disabled: image data is a tuple (filename, bytes)
        """
        try:
            # Create output directory if it doesn't exist and file storage is enabled
            if Settings.ENABLE_FILE_STORAGE and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logging.info(f"Created output directory: {output_dir}")

            # Get the path to the Poppler binaries
            # First, try to find it relative to the current file
            current_dir = Path(__file__).parent.parent.parent.parent.absolute()
            poppler_path = current_dir / "poppler" / "Release-24.08.0-0" / "poppler-24.08.0" / "Library" / "bin"
            
            if not poppler_path.exists():
                # If not found, try the parent directory
                poppler_path = current_dir.parent / "poppler" / "Release-24.08.0-0" / "poppler-24.08.0" / "Library" / "bin"
                
            if poppler_path.exists():
                logging.info(f"Using Poppler binaries from: {poppler_path}")
                # Convert PDF to list of PIL Image objects
                logging.info(f"Converting PDF to images: {pdf_path}")
                images = convert_from_path(pdf_path, dpi=dpi, poppler_path=str(poppler_path))
            else:
                # If Poppler path not found, try without specifying the path
                logging.warning("Poppler path not found, trying without specifying the path")
                images = convert_from_path(pdf_path, dpi=dpi)
                
            logging.info(f"Converted {len(images)} pages from PDF")

            # Process and save each image
            all_image_data = []
            front_page = None

            for i, img in enumerate(images):
                # Generate a filename for this page
                base_filename = os.path.basename(pdf_path)
                page_filename = f"{os.path.splitext(base_filename)[0]}_page_{i+1}.jpg"
                
                if Settings.ENABLE_FILE_STORAGE:
                    # Save to disk if file storage is enabled
                    output_path = os.path.join(output_dir, page_filename)
                    img.save(output_path, "JPEG", quality=95)
                    logging.info(f"Saved image: {output_path}")
                    
                    # Store the file path
                    image_data = output_path
                else:
                    # Store in memory if file storage is disabled
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=95)
                    img_bytes = img_byte_arr.getvalue()
                    
                    # Store the filename and bytes
                    image_data = (page_filename, img_bytes)
                
                all_image_data.append(image_data)
                
                # The first page is the front page
                if i == 0:
                    front_page = image_data

            return front_page, all_image_data

        except Exception as e:
            logging.error(f"Error converting PDF to images: {e}")
            raise 