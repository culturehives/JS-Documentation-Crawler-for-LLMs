# Name: Next.js Documentation Crawler
# Description: This script crawls the Next.js documentation and extracts the content from each page.
# Author: @culturehives
# Last Modified: 2023-05-15
# Python Version: 3.9.6
# Usage: python nextjs_docs.py
# Requirements: pip install requests beautifulsoup4

# Import os module to access the file system
import os
# Import re module to use regular expressions
import re
# Import time module to add delays
import logging
# Import requests module to send HTTP requests
import requests
# Import Function class from functools module to run functions in parallel
import functools
# Import concurrent.futures module to run functions in parallel
import concurrent.futures
# Import BeautifulSoup class from bs4 module to parse HTML content
from bs4 import BeautifulSoup
# Import urljoin function from urllib.parse module to join URLs
from urllib.parse import urljoin

# Base URL of the webpages we will be crawling
base_url = "https://nextjs.org"

# URL of the starting webpage
docs_url = "https://nextjs.org/docs"

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
        content_element = soup.find("div", class_="prose prose-vercel max-w-none")
        # Clean the content
        return clean_content(content_element)
    # Catch all exceptions
    except requests.exceptions.RequestException as e:
        # Log the error
        logging.error(f"Request to {url} failed: {e}")
        # Return None if the request fails
        return None

# Function to get the links from the navbar
def get_links(soup):
    # Create an empty list to store the links
    links_list = []
    # Find the navbar element
    nav_element = soup.select_one("nav.docs-scrollbar")
    # Check if the navbar element exists and has the specified class attribute
    if nav_element:
        # Find all links within the nav element using CSS selectors
        links = nav_element.select("a")
        # Check if links were found
        if links:
            # Get the href attribute of each link and append it to the links list
            for link in links:
                # Get the href attribute of the link
                href = link.get("href")
                # Append the link to the links list
                links_list.append(urljoin(base_url, href))
        else:
            # Log that no links were found in the navbar
            logging.info("No links found in the navbar.")
    else:
        # Log that the navbar element was not found or does not have the specified class attribute
        logging.info("Navbar element not found or does not have the specified class attribute.")
    # Return the links list
    return links_list

# Main function
def main():
    # Send a GET request to the webpage
    response = session.get(docs_url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Get the links from the navbar
    links_list = get_links(soup)

    # Process the links concurrently using threading and multiprocessing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Use functools.partial to create a new function with session pre-filled
        extract_content_with_session = functools.partial(extract_content, session=session)
        # Process the links concurrently using the executor
        content_list = list(executor.map(extract_content_with_session, links_list))

    # Get the content of the first page with the navbar
    content_first = soup.find("div", class_="prose prose-vercel max-w-none")
    # Clean the content of the first page with the navbar
    content_first_cleaned = clean_content(content_first)
    # Insert the content of the first page with the navbar at the beginning of the content list
    content_list.insert(0, content_first_cleaned)

    # Define the script folder and log file path
    script_folder = os.path.dirname(os.path.abspath(__file__))

    # Define the output file path
    output_file_path = os.path.join(script_folder, "export.txt")

    # Save the content list to a text file
    with open(output_file_path, "w") as f:
        # Iterate over the content list
        for content in content_list:
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

# Execute the main function when the script is executed
if __name__ == "__main__":
    # Call the main function
    main()