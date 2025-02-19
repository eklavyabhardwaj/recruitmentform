import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    # Run in headless mode; comment out the following line for visual debugging
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Initialize the WebDriver (adjust chromedriver path if needed)
    driver = webdriver.Chrome(options=options)
    print("Driver initialized.")

    # Define the folder containing PDF files
    current_dir = Path(os.getcwd())
    pdf_folder = current_dir / "Resume Attachments"

    # Get a list of PDFs (using the file stem, i.e., name without extension)
    pdf_files = [file.stem for file in pdf_folder.glob("*.pdf")]
    print(f"Found PDF files: {pdf_files}")

    # Navigate to the login page
    login_url = "https://erpv14.electrolabgroup.com/login#login"
    print(f"Navigating to login page: {login_url}")
    driver.get(login_url)

    # Fill in login credentials and click the login button
    try:
        driver.find_element(By.CSS_SELECTOR, "#login_email").send_keys("slaadmin")
        driver.find_element(By.CSS_SELECTOR, "#login_password").send_keys("slaadmin@123")
        driver.find_element(By.CSS_SELECTOR, ".btn-login").click()
        print("Login form submitted.")
    except Exception as e:
        print(f"Error during login: {e}")
        driver.quit()
        return

    # Wait for login to complete
    time.sleep(6)
    print("Logged in; waited 6 seconds.")

    # Loop through each PDF file
    for pdf in pdf_files:
        pdf_name = pdf
        target_url = f"https://erpv14.electrolabgroup.com/app/job-applicant/{pdf_name}"
        print(f"\nProcessing {pdf_name}: Navigating to {target_url}")
        driver.get(target_url)
        time.sleep(2)

        # Use an XPath that targets the button element with class 'add-attachment-btn'
        # and containing the text 'Attach File'
        xpath_selector = "//button[contains(@class, 'add-attachment-btn') and contains(., 'Attach File')]"
        try:
            print(f"Waiting for 'Attach File' button for {pdf_name} using XPath:\n{xpath_selector}")
            attach_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, xpath_selector))
            )
            attach_button.click()
            print(f"'Attach File' button clicked for {pdf_name}.")
        except Exception as e:
            print(f"Skipping {pdf_name}: 'Attach File' button not found. Exception: {e}")
            continue

        time.sleep(2)

        # Construct the full file path for the PDF to upload
        file_path = str(pdf_folder / f"{pdf_name}.pdf")
        print(f"Uploading file {file_path} for {pdf_name}.")

        # Wait for the file input element and upload the file
        try:
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(file_path)
            print(f"File {file_path} uploaded for {pdf_name}.")
        except Exception as e:
            print(f"Error uploading file for {pdf_name}: {e}")
            continue

        time.sleep(3)

        # Click the confirmation button in the modal dialog
        try:
            print(f"Waiting for confirmation button for {pdf_name}.")
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[type='button'].btn.btn-primary.btn-sm.btn-modal-primary"))
            )
            confirm_button.click()
            print(f"Confirmation button clicked for {pdf_name}.")
        except Exception as e:
            print(f"Error clicking confirmation button for {pdf_name}: {e}")
            continue

        # Wait for the upload process to complete
        time.sleep(5)

        # Delete the PDF file after a successful upload
        try:
            file_to_delete = pdf_folder / f"{pdf_name}.pdf"
            if file_to_delete.exists():
                file_to_delete.unlink()
                print(f"Successfully uploaded & deleted {pdf_name}.pdf")
            else:
                print(f"File {pdf_name}.pdf not found for deletion.")
        except Exception as e:
            print(f"Error deleting {pdf_name}: {e}")

    driver.quit()
    print("Driver closed. Process completed.")


if __name__ == "__main__":
    main()
