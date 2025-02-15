import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os
from pathlib import Path

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set headless to True
        page = await browser.new_page()

        current_dir = Path(os.getcwd())
        pdf_folder = current_dir / "Resume Attachments"

        pdf_files = [file.stem for file in pdf_folder.glob("*.pdf")]

        await page.goto("https://erpv14.electrolabgroup.com/login#login")

        email_address = "slaadmin"
        password = "slaadmin@123"

        await page.fill("#login_email", email_address)
        await page.fill("#login_password", password)

        await page.click(".btn-login")

        await page.wait_for_timeout(6000)

        for pdf in pdf_files:
            pdf_name = pdf
            target_url = f"https://erpv14.electrolabgroup.com/app/job-applicant/{pdf_name}"

            await page.goto(target_url)
            await page.wait_for_timeout(2000)

            try:
                await page.wait_for_selector("span.pill-label.ellipsis:has-text('Attach File')", timeout=10000)
                await page.click("span.pill-label.ellipsis:has-text('Attach File')")
            except TimeoutError:
                print(f"Skipping {pdf_name}: 'Attach File' button not found")
                continue

            await page.wait_for_timeout(2000)
            file_path = str(pdf_folder / f"{pdf_name}.pdf")

            file_input_selector = "input[type='file']"
            await page.set_input_files(file_input_selector, file_path)
            await page.wait_for_timeout(3000)

            await page.click("button[type='button'].btn.btn-primary.btn-sm.btn-modal-primary")
            await page.wait_for_timeout(5000)

            try:
                file_to_delete = pdf_folder / f"{pdf_name}.pdf"
                if file_to_delete.exists():
                    file_to_delete.unlink()
                    print(f"Successfully uploaded & Deleted {pdf_name}.pdf")
            except Exception as e:
                print(f"Error deleting {pdf_name}: {e}")

        await browser.close()

# Run the async function
asyncio.run(run())
