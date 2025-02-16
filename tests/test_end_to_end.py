import builtins
import sys

# Patch the built-in print to filter out unwanted log messages
_original_print = builtins.print

def filtered_print(*args, **kwargs):
    message = " ".join(str(arg) for arg in args)
    # List any prefixes you want to filter out. Adjust this list as needed.
    skip_prefixes = ("[DEBUG]", "Found image files:", "Found JSON files:")
    if any(message.startswith(prefix) for prefix in skip_prefixes):
        return  # Skip printing this message
    _original_print(*args, **kwargs)

builtins.print = filtered_print

import os
# Force disk persistence mode by setting the environment variable early.
os.environ["ENABLE_FILE_STORAGE"] = "True"

import glob
import unittest
import json
import importlib
import logging
from unittest.mock import patch

from statementAIPArser import main as main_module
from statementAIPArser.config import Config
from statementAIPArser.assistant_client import AssistantClient  # use actual client

# Configure logging to output to both console and a log file.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_results.log", mode="w")
    ]
)

# ANSI escape sequences for colors
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"

class LoggingTextTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        message = f"{GREEN}PASSED: {test}{RESET}"
        # Write directly to the unbuffered stdout to bypass capturing
        sys.__stdout__.write(message + "\n")
        sys.__stdout__.flush()
        logging.info(message)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        # self.failures[-1][1] contains the error message.
        message = f"{RED}FAILED: {test} - {self.failures[-1][1]}{RESET}"
        sys.__stdout__.write(message + "\n")
        sys.__stdout__.flush()
        logging.error(message)

    def addError(self, test, err):
        super().addError(test, err)
        message = f"{RED}ERROR: {test} - {self.errors[-1][1]}{RESET}"
        sys.__stdout__.write(message + "\n")
        sys.__stdout__.flush()
        logging.error(message)

class TestEndToEndProcess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Use a fixed output directory so that files remain available after the test run.
        cls.test_output_dir = r"C:\Users\cbyro\OneDrive\cursorWorkspace\statementAIParser\statementAIPArser\processing"
        os.makedirs(cls.test_output_dir, exist_ok=True)
        
        # Clean up any .json, .jpg, or .png files in the directory before starting tests.
        for filename in os.listdir(cls.test_output_dir):
            if filename.endswith(".json") or filename.endswith(".jpg") or filename.endswith(".png"):
                os.remove(os.path.join(cls.test_output_dir, filename))
        
        # Ensure disk storage is enabled.
        os.environ["ENABLE_FILE_STORAGE"] = "True"
        Config.ENABLE_FILE_STORAGE = True
        Config.OUTPUT_DIR = cls.test_output_dir

    def setUp(self):
        # Patch os.path.join to use a fixed processing directory.
        self.original_join = os.path.join
        def fake_join(*args, **kwargs):
            if len(args) == 2 and args[0] == "processing":
                return self.__class__.test_output_dir
            return self.original_join(*args, **kwargs)
        self.join_patcher = patch("statementAIPArser.main.os.path.join", side_effect=fake_join)
        self.join_patcher.start()
        
        # Reload modules that may have cached configuration values.
        import statementAIPArser.pdf_utils as pdf_utils
        importlib.reload(pdf_utils)
        importlib.reload(main_module)

    def tearDown(self):
        # Stop our join patcher.
        self.join_patcher.stop()
        # NOTE: Do NOT clean the output folder so that files remain for verification.

    def test_01_full_end_to_end(self):
        # Path to the test PDF file.
        test_pdf_path = os.path.abspath(
            os.path.join("statementAIPArser", "test_data", "Statement_163322_10212003_27_Jun_2024.pdf")
        )
        if not os.path.exists(test_pdf_path):
            self.skipTest("Test PDF file does not exist: " + test_pdf_path)

        # Create a real instance of AssistantClient.
        # WARNING: This will attempt to send images to OpenAI. Ensure you have valid API credentials.
        client = AssistantClient(
            api_key=Config.OPENAI_API_KEY,
            assistant_id=Config.ASSISTANT_ID
        )

        # Run the full end-to-end pipeline.
        responses = main_module.process_single_file(test_pdf_path, client)

        # ========= Assertion 1: Check that 12 PNG images were created.
        image_files = [f for f in os.listdir(self.__class__.test_output_dir) if f.endswith('.png')]
        print("Found image files:", image_files)
        self.assertEqual(len(image_files), 12, "Expected 12 images to be converted from the PDF")

        # ========= Assertion 2: Check that the expected number of JSON responses were created.
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_*.json"))
        print("Found JSON files:", json_files)
        self.assertEqual(len(json_files), 12, "Expected 12 JSON files to be received back from OpenAI")
        
        # ========= Assertion 3: Check that the final merged JSON file was created.
        final_json_path = os.path.join(self.__class__.test_output_dir, "final_statement_data.json")
        self.assertTrue(os.path.exists(final_json_path),
                        "Expected final merged JSON file to be created at: " + final_json_path)

    def test_02_png_image_count(self):
        """Check that the expected number of PNG images are produced."""
        image_files = [f for f in os.listdir(self.__class__.test_output_dir) if f.endswith('.png')]
        print("Found image files:", image_files)
        self.assertEqual(len(image_files), 12, "Expected 12 images to be converted from the PDF")
    
    def test_03_json_response_count(self):
        """Check that the expected number of JSON responses were created."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_*.json"))
        print("Found JSON files:", json_files)
        self.assertEqual(len(json_files), 12, "Expected 12 JSON files to be received back from OpenAI")
        
    def test_04_final_json_created(self):
        """Check that the final merged JSON file is present in the processing directory."""
        final_json_path = os.path.join(self.__class__.test_output_dir, "final_statement_data.json")
        self.assertTrue(os.path.exists(final_json_path),
                        "Expected final merged JSON file to be created at: " + final_json_path)

    def test_05_front_page_transactions(self):
        """Check that the first page JSON contains exactly 20 transactions."""
        # Find the front page JSON file
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_front_*.json"))
        self.assertTrue(json_files, "No front page JSON file found")
        json_path = json_files[0]  # Take the first matching file
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 20, "Expected 20 transactions in first page JSON")

    def test_06_page_two_transactions(self):
        """Check that the second page JSON contains exactly 33 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page2_*.json"))
        self.assertTrue(json_files, "No page 2 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 33, "Expected 33 transactions in second page JSON")

    def test_07_page_three_transactions(self):
        """Check that the third page JSON contains exactly 32 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page3_*.json"))
        self.assertTrue(json_files, "No page 3 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 32, "Expected 32 transactions in third page JSON")

    def test_08_page4_transactions(self):
        """Check that the fourth page JSON contains exactly 32 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page4_*.json"))
        self.assertTrue(json_files, "No page 4 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 32, "Expected 32 transactions in fourth page JSON")

    def test_09_page5_transactions(self):
        """Check that the fifth page JSON contains exactly 31 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page5_*.json"))
        self.assertTrue(json_files, "No page 5 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 31, "Expected 31 transactions in fifth page JSON")

    def test_10_page6_transactions(self):
        """Check that the sixth page JSON contains exactly 33 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page6_*.json"))
        self.assertTrue(json_files, "No page 6 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 33, "Expected 33 transactions in sixth page JSON")

    def test_11_page7_transactions(self):
        """Check that the seventh page JSON contains exactly 30 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page7_*.json"))
        self.assertTrue(json_files, "No page 7 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 30, "Expected 30 transactions in seventh page JSON")

    def test_12_page8_transactions(self):
        """Check that the eighth page JSON contains exactly 32 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page8_*.json"))
        self.assertTrue(json_files, "No page 8 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 32, "Expected 32 transactions in eighth page JSON")

    def test_13_page9_transactions(self):
        """Check that the ninth page JSON contains exactly 33 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page9_*.json"))
        self.assertTrue(json_files, "No page 9 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 33, "Expected 33 transactions in ninth page JSON")

    def test_14_page10_transactions(self):
        """Check that the tenth page JSON contains exactly 29 transactions."""
        json_files = glob.glob(os.path.join(self.__class__.test_output_dir, "statement_analysis_page10_*.json"))
        self.assertTrue(json_files, "No page 10 JSON file found")
        json_path = json_files[0]
        with open(json_path, 'r') as f:
            data = json.load(f)
            transactions = data.get('Transactions', [])
            self.assertEqual(len(transactions), 29, "Expected 29 transactions in tenth page JSON")

if __name__ == '__main__':
    # Create a TextTestRunner with increased verbosity, disabling buffering.
    runner = unittest.TextTestRunner(verbosity=2, failfast=False, buffer=False, resultclass=LoggingTextTestResult)
    unittest.main(testRunner=runner) 