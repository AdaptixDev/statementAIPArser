import os
import unittest
from pdf_utils import PDFConverter

class TestPDFConversion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.output_dir = "converted_images"
        os.makedirs(cls.output_dir, exist_ok=True)
        cls.pdf_path = "Statement_163322_10212003_27_Jun_2024.pdf"
        
        # If the PDF doesn't exist, skip all tests in this class.
        if not os.path.exists(cls.pdf_path):
            raise unittest.SkipTest(f"PDF file {cls.pdf_path} does not exist. Please add a PDF file to test the conversion.")
        
        # Perform the PDF conversion once.
        cls.front_page, cls.images = PDFConverter.pdf_to_images(cls.pdf_path, cls.output_dir)

    def test_pdf_file_exists(self):
        """Test if the PDF file exists."""
        self.assertTrue(os.path.exists(self.pdf_path),
                        f"PDF file {self.pdf_path} does not exist. Please add a PDF file to test the conversion.")

    def test_conversion_produces_images(self):
        """Test that PDF conversion produces a non-empty list of images."""
        # Check that the conversion result is not None.
        self.assertIsNotNone(self.images, "PDF conversion did not produce any results.")
        # Check that at least one image was converted.
        self.assertGreater(len(self.images), 0, 
                           f"Expected at least one image from PDF conversion, got {len(self.images)}")

    def test_all_converted_images_exist(self):
        """For disk storage mode, test that each converted image exists on disk."""
        # If we're running in disk storage mode the images are file paths (strings).
        if self.images and isinstance(self.images[0], str):
            for image_path in self.images:
                self.assertTrue(os.path.exists(image_path),
                                f"Converted image {image_path} not found on disk.")

if __name__ == "__main__":
    unittest.main()
