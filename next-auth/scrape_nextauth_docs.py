import requests
from bs4 import BeautifulSoup
import re
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

# URL of the webpage to scrape
base_url = "https://next-auth.js.org"
docs_url = "https://next-auth.js.org/getting-started/introduction#"

# Set up a requests session
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# Set up logging with the log file in the script's folder
script_folder = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_folder, "log.log")

logging.basicConfig(filename=log_file_path, level=logging.INFO)

# Precompile regex
whitespace_regex = re.compile(r'\s+')
sentence_regex = re.compile(r'^.*?[.!?]')
last_sentence_regex = re.compile(r'[A-Z][^.!?]*[.!?]')

def clean_content(content_element):
    if content_element:
        for code_element in content_element.select('code'):
            # Wrap code element text in backticks
            code_element.string = f'```{code_element.get_text()}```'
        # Clean the content by removing excessive whitespace and line breaks
        content = ' '.join(content_element.stripped_strings)
        content = whitespace_regex.sub(' ', content)
        content = content.replace('\n', ' ')
        return content
    else:
        return None

def extract_content(url, session):
    try:
        response = session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        content_element = soup.find("div", class_="theme-doc-markdown markdown")
        return clean_content(content_element)
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to {url} failed: {e}")
        return None

def get_links(driver):
    links_set = set()  # Use a set to store unique links
    links_list = []    # Use a list to preserve order

    def process_menu_item(menu_item):
        # Try to get the link inside the menu item
        try:
            link = menu_item.find_element(By.CSS_SELECTOR, 'a')
            # Get the href attribute
            href = link.get_attribute('href')
            if href and not href.startswith('#') and 'carbonads.net' not in href:  # Exclude '#' links
                clean_href = href.split('#')[0]    # Remove the fragment identifier
                if clean_href not in links_set:    # Check for duplicates
                    links_set.add(clean_href)
                    links_list.append(clean_href)
        except NoSuchElementException:
            pass

        # Check if the menu item is collapsed
        is_collapsed = 'collapsed' in menu_item.get_attribute('class')

        # If it is, click it to expand
        if is_collapsed:
            menu_item.click()
            time.sleep(1)  # Wait for the menu to expand

        # Try to find nested ul
        try:
            nested_ul = menu_item.find_element(By.CSS_SELECTOR, 'ul')
            nested_li = nested_ul.find_elements(By.CSS_SELECTOR, 'li')
            for item in nested_li:
                process_menu_item(item)
        except NoSuchElementException:
            pass  # If there is no nested ul, then just pass

    # Get the first-level menu items
    menu_items = driver.find_elements(By.CSS_SELECTOR, 'nav.menu > ul > li')

    # Iterate over the menu items in order
    for menu_item in menu_items:
        process_menu_item(menu_item)

    return links_list

def main():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"  # Update this path

    # Set up ChromeDriver service
    webdriver_service = Service(ChromeDriverManager().install())

    # Initialize the webdriver
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.get(docs_url)

    # Get the links
    links_list = get_links(driver)

    # # Log all found URLs
    # logging.info("Found URLs:")
    # for url in links_list:
    #     logging.info(url)

    # Process the links sequentially
    content_list = []
    for link in links_list:
        content = extract_content(link, session)
        content_list.append(content)

    # Save the content list to a text file in the script's folder
    script_folder = os.path.dirname(os.path.abspath(__file__))
    output_file_path = os.path.join(script_folder, "export.txt")

    with open(output_file_path, "w") as f:
        for content in content_list:
            if content:  # Only write content that is not None
                f.write(content + "\n")

    # Print the content list and calculate the total character count
    logging.info("Content list:")
    for content in content_list:
        if content:
            logging.info(content)

    total_characters = sum(len(content) for content in content_list if content)
    logging.info("Total character count: %s", total_characters)

    # Print the first and last sentences
    if content_list:
        first_sentence = sentence_regex.match(content_list[0])
        last_sentence = last_sentence_regex.findall(content_list[-1])[-1] if content_list[-1] else None

        logging.info("First Sentence: %s", first_sentence.group() if first_sentence else "N/A")
        logging.info("Last Sentence: %s", last_sentence if last_sentence else "N/A")
    else:
        logging.info("Content list is empty.")

    # Close the Selenium WebDriver
    driver.quit()

if __name__ == "__main__":
    main()
