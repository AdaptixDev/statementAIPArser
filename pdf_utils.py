
import os
from typing import List
from pdf2image import convert_from_path
from PIL import Image

class PDFConverter:
    @staticmethod
    def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 300) -> List[str]:
        """
        Convert PDF file to high quality images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the images
            dpi: Resolution for the output images (default: 300)
            
        Returns:
            List of paths to the generated images
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=dpi)
        
        # Save images
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(
                output_dir, 
                f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{i+1}.jpg"
            )
            image.save(image_path, "JPEG", quality=95)
            image_paths.append(image_path)
            
        return image_paths
