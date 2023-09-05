"""
This module defines a class 'Superside' that inherits from 'BaseProcessing' and handles the processing of HTML files.

The 'run' method retrieves file paths, reads files and loads their content as JSON, and extracts certain elements from
the HTML using XPath. It then updates or inserts these items into a collection.

The script also sets up command line arguments for controlling full-load and debug operations.
"""

import argparse
from dataclasses import dataclass
from datetime import datetime

from loguru import logger
from lxml import html

from processing._base import BaseProcessing


@dataclass
class Superside(BaseProcessing):
    """
    Extends BaseProcessing for processing HTML files.

    Attributes
    ----------
        (Inherited from BaseProcessing)
    """

    def run(self) -> None:
        """
        Processes HTML files from the S3 path 'pages/Superside', extracting specific elements
        from each HTML and updating or inserting the data into a MongoDB collection.

        HTML elements extracted include the title, description, and text content, identified using XPath.

        Each item in the MongoDB collection consists of the URL, title, description, texts, and timestamp.

        Returns
        -------
        None
        """
        files = self.s3.list_files_from_path(f"pages/{self.company}")

        for file in files:
            logger.debug(f"Processing file: {file}")
            file_contents = self.s3.read_json(path=file)
            tree = html.fromstring(file_contents.get("content"))

            title = self.extract_text_by_xpath(tree, '//meta[@property="og:title"]//@content')
            description = self.extract_text_by_xpath(tree, '//meta[@name="description"]//@content')
            texts = self.extract_text_by_xpath(tree, "//p//text()")

            item = {
                "url": file_contents.get("url"),
                "title": title,
                "description": description,
                "texts": texts,
                "updated_at": datetime.now(),
            }

            self.collection.replace_one(filter={"url": item.get("url")}, replacement=item, upsert=True)


if __name__ == "__main__":
    """
    Parses command-line arguments and starts the processing using an instance of the Superside class.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-load", default=False, action="store_true", dest="full_load")
    parser.add_argument("--debug", default=False, action="store_true", dest="debug")
    args = parser.parse_args()

    logger.info("Starting Superside processing...")

    superside = Superside(company="Superside", full_load=args.full_load, debug=args.debug)
    superside.run()

    logger.info("Finished Superside processing!")
