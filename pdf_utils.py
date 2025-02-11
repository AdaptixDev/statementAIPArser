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
            Tuple containing (first_page_path, list_of_all_image_paths)
        """
        logging.info(f"Starting PDF conversion for: {pdf_path}")
        if not os.path.exists(output_dir):
            logging.info(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)

        logging.info("Converting PDF to images...")
        # Convert PDF to images with enhanced quality
        images = convert_from_path(
            pdf_path,
            dpi=600,  # Increased DPI for better resolution
            thread_count=2,  # Use multiple threads for faster processing
            fmt="jpeg"  # Explicitly set format
        )
        logging.info(f"Successfully converted PDF to {len(images)} images")

        # Save images with maximum quality
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(
                output_dir, 
                f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{i+1}.jpg"
            )
            logging.info(f"Saving image {i+1} to: {image_path}")
            image.save(image_path, "JPEG", quality=100, optimize=False)
            image_paths.append(image_path)

        logging.info("PDF conversion completed successfully")
        return (image_paths[0], image_paths) if image_paths else (None, [])