# Name: NextAuth.js Documentation Crawler
# Description: This script crawls the NextAuth.js documentation and extracts the content from each page.
# Author: @culturehives
# Last Modified: 2023-05-15
# Python Version: 3.9.6
# Usage: python nextauth_docs.py
# Requirements: pip install requests beautifulsoup4 selenium webdriver_manager
# Notes: This script was intended to be run on a Mac using the Brave Browser.
#        You will need to install the Brave Browser or Google Chrome and the ChromeDriver for Selenium.
#        You can download the ChromeDriver from https://chromedriver.chromium.org/downloads.
#        You will need to change the path to the ChromeDriver in the script on line 178.
#        You will also need to install the Python packages listed above.

# Import os module to access the file system
import os
# Import re module to use regular expressions
import re
# Import time module to add delays
import time
# Import logging module to log errors
import logging
# Import requests module to send HTTP requests
import requests
# Import BeautifulSoup class from bs4 module to parse HTML content
from bs4 import BeautifulSoup
# Import Selenium WebDriver API module to automate the browser
from selenium import webdriver
# Import Service class from selenium.webdriver.chrome.service module to start the ChromeDriver server
from selenium.webdriver.chrome.service import Service
# Import Options class from selenium.webdriver.chrome.options module to set options for the browser
from selenium.webdriver.chrome.options import Options
# Import ChromeDriverManager class from webdriver_manager.chrome module to download the latest version of the ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager
# Import NoSuchElementException class from selenium.common.exceptions module to handle exceptions
from selenium.common.exceptions import NoSuchElementException
# Import By class from selenium.webdriver.common.by module to specify the search criteria
from selenium.webdriver.common.by import By

# Base URL of the webpages we will be crawling
base_url = "https://next-auth.js.org"

# URL of the starting webpage
docs_url = "https://next-auth.js.org/getting-started/introduction#"

# Set up a session with requests to reuse the same TCP connection
session = requests.Session()

# Set a custom user agent to avoid being blocked by the server
session.headers.update({"User-Agent": "Mozilla/5.0"})

# Define the script folder and log file path
script_folder = os.path.dirname(os.path.abspath(__file__))

# Create a log file in the script's folder
log_file_path = os.path.join(script_folder, "log.log")

# Set up logging with the log file in the script's folder
logging.basicConfig(filename=log_file_path, level=logging.INFO)

# Regex used to clean the whitespace from the content
whitespace_regex = re.compile(r'\s+')

# Regex used to extract the first sentence of the content
sentence_regex = re.compile(r'^.*?[.!?]')

# Regex used to extract the last sentence of the content
last_sentence_regex = re.compile(r'[A-Z][^.!?]*[.!?]')

# Function to clean the content
def clean_content(content_element):
    # Check if the content element exists
    if content_element:
        # Find all code elements within the content element
        for code_element in content_element.select('code'):
            # Wrap code element text in backticks
            code_element.string = f'```{code_element.get_text()}```'
        # Clean the content by removing excessive whitespace and line breaks
        content = ' '.join(content_element.stripped_strings)
        # Replace multiple spaces with a single space
        content = whitespace_regex.sub(' ', content)
        # Replace line breaks with a single space
        content = content.replace('\n', ' ')
        # Return the cleaned content
        return content
    else:
        # Return None if the content element does not exist
        return None

# Function to extract the content from the webpage
def extract_content(url, session):
    try:
        # Send a GET request to the webpage
        response = session.get(url)
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the content element
        content_element = soup.find("div", class_="theme-doc-markdown markdown")
        # Clean the content
        return clean_content(content_element)
    # Catch the exception if the request fails
    except requests.exceptions.RequestException as e:
        # Log the error
        logging.error(f"Request to {url} failed: {e}")
        # Return None if the request fails
        return None

# Function to get the links from the navbar
def get_links(driver):
    # Set up a set to store the links
    links_set = set()

    # Create an empty list to store the links
    links_list = []

    # Function to process a menu item
    def process_menu_item(menu_item):
        # Try to get the link inside the menu item
        try:
            # Find the link
            link = menu_item.find_element(By.CSS_SELECTOR, 'a')
            # Get the href attribute
            href = link.get_attribute('href')
            # Check if the link is valid
            if href and not href.startswith('#') and 'carbonads.net' not in href:
                # Clean the href by removing the anchor
                clean_href = href.split('#')[0]
                # Check if the link is not already in the set
                if clean_href not in links_set:
                    # Add the link to the set
                    links_set.add(clean_href)
                    # Add the link to the list
                    links_list.append(clean_href)
        # Catch the exception if the link does not exist
        except NoSuchElementException:
            # If there is no link, then move on
            pass

        # Check if the menu item is collapsed
        is_collapsed = 'collapsed' in menu_item.get_attribute('class')

        # If it is, click it to expand
        if is_collapsed:
            # Click the link
            menu_item.click()
            # Wait for 1 second before continuing
            time.sleep(1)

        # Try to find nested ul
        try:
            # Find the nested ul
            nested_ul = menu_item.find_element(By.CSS_SELECTOR, 'ul')
            # Find all nested li
            nested_li = nested_ul.find_elements(By.CSS_SELECTOR, 'li')
            # Iterate over the nested li
            for item in nested_li:
                # Process the nested li
                process_menu_item(item)
        # Catch the exception if the nested ul does not exist        
        except NoSuchElementException:
            # If there is no nested ul, then move on
            pass

    # Get the first-level menu items
    menu_items = driver.find_elements(By.CSS_SELECTOR, 'nav.menu > ul > li')

    # Iterate over the menu items in order
    for menu_item in menu_items:
        # Process the menu item
        process_menu_item(menu_item)
    # Return the list of links
    return links_list

def main():
    # Set up Chrome options
    chrome_options = Options()
    
    # Define the path to the Brave browser executable
    chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    # Set up ChromeDriver service
    webdriver_service = Service(ChromeDriverManager().install())

    # Initialize the webdriver
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    
    # Define the URL of the documentation
    driver.get(docs_url)

    # Get the links from the navbar
    links_list = get_links(driver)

    # Create a list to store the content
    content_list = []
    # Iterate over the links
    for link in links_list:
        # Extract the content from the link
        content = extract_content(link, session)
        # Add the content to the list
        content_list.append(content)

   # Define the script folder and log file path
    script_folder = os.path.dirname(os.path.abspath(__file__))

    # Define the output file path
    output_file_path = os.path.join(script_folder, "export.txt")

    # Save the content list to a text file
    with open(output_file_path, "w") as f:
        # Iterate over the content list
        for content in content_list:
            # Check if the content exists
            if content:
                # Write the content to the file
                f.write(content + "\n")

    # Iterate over the content list
    for content in content_list:
        # Check if the content exists
        if content:
            # Log the content
            logging.info(content)

    # Calculate the total character count
    total_characters = sum(len(content) for content in content_list if content)
    # Log the total character count
    logging.info("Total character count: %s", total_characters)

    # Check if the content list is not empty
    if content_list:
        # Get the first sentence of the first page
        first_sentence = sentence_regex.match(content_list[0])
        # Get the last sentence of the last page
        last_sentence = last_sentence_regex.findall(content_list[-1])[-1] if content_list[-1] else None
        # Log the first setence
        logging.info("First Sentence: %s", first_sentence.group() if first_sentence else "N/A")
        # Log the last sentence
        logging.info("Last Sentence: %s", last_sentence if last_sentence else "N/A")
    else:
        # Log that the content list is empty
        logging.info("Content list is empty.")

    # Close the Selenium WebDriver
    driver.quit()

# Execute the main function when the script is executed
if __name__ == "__main__":
    # Call the main function
    main()
