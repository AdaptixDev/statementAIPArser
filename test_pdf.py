
from pdf_utils import PDFConverter
import os

def test_pdf_conversion():
    # Create output directory
    output_dir = "converted_images"
    
    # Test PDF file path - you'll need to add a PDF file to test
    pdf_path = "Statement_163322_10212003_27_Jun_2024.pdf"
    
    if os.path.exists(pdf_path):
        try:
            # Convert PDF to images
            image_paths = PDFConverter.pdf_to_images(pdf_path, output_dir)
            print(f"Successfully converted PDF to {len(image_paths)} images:")
            for path in image_paths:
                print(f"- {path}")
        except Exception as e:
            print(f"Error converting PDF: {str(e)}")
    else:
        print(f"Please add a PDF file named {pdf_path} to test the conversion")

if __name__ == "__main__":
    test_pdf_conversion()
