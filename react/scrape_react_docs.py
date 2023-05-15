import requests
from bs4 import BeautifulSoup
import concurrent.futures
import os
import re
import functools
import logging
from urllib.parse import urljoin

# URL of the webpage to scrape
base_url = "https://react.dev"
docs_url = "https://react.dev/learn"

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
        content_element = soup.find('article')
        return clean_content(content_element)
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to {url} failed: {e}")
        return None

def get_links(soup):
    links_list = []
    nav_element = soup.find('nav', {'role': 'navigation'})
    if nav_element:
        # Find all links within the nav element using CSS selectors
        links = nav_element.select("a")
        if links:
            for link in links:
                href = link.get("href")
                links_list.append(urljoin(base_url, href))
        else:
            logging.info("No links found in the navbar.")
    else:
        logging.info("Navbar element not found or does not have the specified class attribute.")
    return links_list

def main():
    # Send a GET request to the webpage
    response = session.get(docs_url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    links_list = get_links(soup)

    # Process the links concurrently using threading and multiprocessing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Use functools.partial to create a new function with session pre-filled
        extract_content_with_session = functools.partial(extract_content, session=session)
        content_list = list(executor.map(extract_content_with_session, links_list))

    # Get the content of the first page with the navbar
    content_first = soup.find('article')
    content_first_cleaned = clean_content(content_first)
    content_list.insert(0, content_first_cleaned)

    # Save the content list to a text file in the script's folder
    script_folder = os.path.dirname(os.path.abspath(__file__))
    output_file_path = os.path.join(script_folder, "export.txt")

    # Save the content list to a text file
    with open(output_file_path, "w") as f:
        for content in content_list:
            f.write(content + "\n")

    # Print the content list and calculate the total character count
    logging.info("Content list:")
    for content in content_list:
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

if __name__ == "__main__":
    main()