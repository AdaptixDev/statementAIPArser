import os
import logging
from typing import List, Tuple, Union
from pdf2image import convert_from_path
from PIL import Image
from io import BytesIO

# Import the config so we can check our storage toggle.
from config import Config

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
            When disabled: image data is a tuple (pseudo_filename, image_bytes)
        """
        logging.info(f"Starting PDF conversion for: {pdf_path}")
        
        # Create output directory only if writing to disk.
        if Config.ENABLE_FILE_STORAGE and not os.path.exists(output_dir):
            logging.info(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)

        # Explicit poppler path for Windows - update as needed.
        poppler_path = r"C:\Users\cbyro\OneDrive\cursorWorkspace\statementAIParser\poppler\Release-24.08.0-0\poppler-24.08.0\library\bin"
        
        if not os.path.exists(poppler_path):
            raise ValueError(f"Poppler path does not exist: {poppler_path}")
        
        logging.info(f"Using poppler path: {poppler_path}")
        logging.info("Converting PDF to images...")

        try:
            # Convert the PDF to high resolution images.
            images = convert_from_path(
                pdf_path,
                poppler_path=poppler_path,
                dpi=dpi,
                thread_count=2,
                fmt="png"
            )
            logging.info(f"Successfully converted PDF to {len(images)} image(s)")
    
            # Use the images directly without contrast enhancement.
            if Config.ENABLE_FILE_STORAGE:
                image_paths = []
                for i, image in enumerate(images):
                    if i == 0:
                        image_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_front.png"
                    else:
                        image_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{i+1}.png"
                    image_path = os.path.join(output_dir, image_filename)
                    logging.info(f"Saving image {i+1} to: {image_path}")
                    image.save(image_path, "PNG")
                    image_paths.append(image_path)
    
                logging.info("PDF conversion completed successfully (disk storage enabled)")
                return (image_paths[0], image_paths) if image_paths else (None, [])
            else:
                logging.info("File storage disabled: images will be kept in memory.")
                images_in_memory = []
                for i, image in enumerate(images):
                    if i == 0:
                        pseudo_name = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_front.png"
                    else:
                        pseudo_name = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{i+1}.png"
    
                    bio = BytesIO()
                    image.save(bio, format='PNG')
                    image_bytes = bio.getvalue()
                    logging.info(f"Image {i+1} stored in memory with indicator: {pseudo_name}")
                    images_in_memory.append((pseudo_name, image_bytes))
    
                logging.info("PDF conversion completed successfully (in-memory storage)")
                front_image = images_in_memory[0] if images_in_memory else None
                return (front_image, images_in_memory)
            
        except Exception as e:
            logging.error(f"Error during PDF conversion: {str(e)}")
            if not os.path.exists(pdf_path):
                logging.error(f"PDF file does not exist: {pdf_path}")
            elif not os.access(pdf_path, os.R_OK):
                logging.error(f"PDF file is not readable: {pdf_path}")
            raise