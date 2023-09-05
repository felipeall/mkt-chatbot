"""
This module defines the `BaseProcessing` class which provides core functionality for processing HTML files.

The class has methods to connect to MongoDB, set logger level, filter valid files from a directory, extract text
data from HTML using XPath and clean HTML text.
"""

import json
import re
import sys
from dataclasses import dataclass
from glob import glob
from typing import Optional

from loguru import logger
from lxml.html import HtmlElement
from nested_lookup import nested_lookup
from pymongo import MongoClient

from aws.s3 import AWSS3


@dataclass
class BaseProcessing:
    """
    A base class for processing HTML files.

    Attributes
    ----------
        company (str): Name of the company for which the HTML files are being processed.
        full_load (bool): If True, drops the MongoDB collection before processing.
        debug (bool): If True, sets the logger level to 'DEBUG'. If False, 'INFO'.
        database (str): Name of the MongoDB database. Defaults to "data".
        invalid_pages (tuple): Tuple of substrings that determine invalid file paths.
    """

    company: str
    full_load: bool
    debug: bool
    database: str = "data"
    invalid_pages: tuple = (
        "-blog-author-",
        "-blog-authors-",
        "-blog-category-",
        "-blog-tag-",
    )

    def __post_init__(self) -> None:
        """
        Initializes the MongoDB connection and sets the logger level.
        This method is called automatically after the class is instantiated.
        """
        self._set_logger_level()
        self._connect_mongodb()
        self.s3 = AWSS3()

    def _connect_mongodb(self) -> None:
        """
        Establishes a connection to MongoDB. The MongoClient instance is connected to the default host
        and port and the `database` attribute is used to specify the database. A collection is
        initialized in the database using the `company` attribute. If `full_load` attribute is True,
        the existing collection is dropped before processing.
        """
        logger.info("Instantiating MongoDB connection...")
        client = MongoClient()
        db = client[self.database]
        self.collection = db[self.company]
        if self.full_load:
            self.log.info(f"Dropped collection: {self.company}")
            self.collection.drop()
        self.log.info("Instantiated MongoDB connection!")

    def _set_logger_level(self) -> None:
        """
        Sets the level of the logger. If `debug` attribute is True, the logger level is set to "DEBUG",
        else it is set to "INFO".
        """
        self.log = logger
        self.log.remove()
        self.log.add(sys.stderr, level="DEBUG" if self.debug else "INFO")

    def get_files_paths(self) -> list:
        """
        Returns a list of valid file paths from the `datalake` directory. It filters out file paths that
        contain any substring specified in the `invalid_pages` attribute.
        """
        files = glob(f"datalake/{self.company}/*.json")
        files_valid = [file for file in files if not any(substring in file for substring in self.invalid_pages)]
        self.log.info(f"Number of html files found: {len(files_valid)}")
        return files_valid

    def extract_next_data(self, tree: HtmlElement) -> Optional[list]:
        """
        Extracts data from the "__NEXT_DATA__" script tag in the provided HTML tree.
        It looks for 'paragraph', 'body', 'content', and 'title' keys in the parsed JSON data.
        The values associated with these keys are cleaned of any HTML tags and concatenated into a single string.

        Args:
            tree (HtmlElement): An lxml HtmlElement from which data is to be extracted.

        Returns
        -------
            Optional[str]: A string containing the cleaned and concatenated text, or None if no such data is found.
        """
        data = tree.xpath("//script[@id='__NEXT_DATA__']//text()")[0]
        data_parsed = json.loads(data)
        paragraph = nested_lookup("paragraph", data_parsed)
        body = nested_lookup("body", data_parsed)
        content = nested_lookup("content", data_parsed)
        nested_lookup("title", data_parsed)

        next_data = []
        next_data.extend(paragraph)
        next_data.extend(body)
        next_data.extend(content)

        next_data_cleaned = [self.cleanhtml(text.strip()) for text in next_data if text]
        next_data_text = " ".join(next_data_cleaned).replace("\n", "").replace("&nbsp;", "")

        return next_data_text or None

    @staticmethod
    def cleanhtml(text: str) -> str:
        """
        Cleans a given text string from HTML tags. This is achieved by applying a regular expression that
        matches any text within '<' and '>'. All matched substrings are replaced with an empty string,
        effectively removing all HTML tags.

        Args:
            text (str): The text string from which HTML tags are to be removed.

        Returns
        -------
            str: The cleaned text string.
        """
        return re.sub(re.compile("<.*?>"), "", text)

    @staticmethod
    def extract_text_by_xpath(tree: HtmlElement, selector: str) -> Optional[str]:
        """
        Extracts text data from the provided HTML tree using the provided XPath selector.
        The extracted data is joined into a single string.

        Args:
            tree (HtmlElement): An lxml HtmlElement from which data is to be extracted.
            selector (str): An XPath selector used to locate the data in the HTML tree.

        Returns
        -------
            Optional[str]: A string containing the joined text data, or None if no data is found using the selector.
        """
        data = tree.xpath(selector)
        if not data:
            return None
        return " ".join(data).replace("\n", "").replace("&nbsp;", "")
