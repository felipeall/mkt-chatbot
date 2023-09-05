"""
This module contains a specific implementation of Scrapy's CrawlSpider for the superside.com domain.

It is designed to crawl the pages on the website, parse the HTML response, and store the parsed data (specifically,
the URL and the HTML content) in JSON files.

Each JSON file is named after the URL of the crawled webpage (cleaned to be ASCII compliant) and is saved in AWS S3
bucket.
"""

from dotenv import load_dotenv
from scrapy.http import HtmlResponse
from scrapy.spiders import CrawlSpider, Rule

from aws.s3 import AWSS3

load_dotenv()


class SupersideSpider(CrawlSpider):
    """
    SupersideSpider is a Scrapy spider for crawling the superside.com website.
    It follows the rules specified in the 'rules' tuple, which instructs the spider to call 'parse_item' for each
    crawled page and follow any links for further crawling.

    Attributes:
    name: A string representing the name of the spider. Used in logging and statistics collection.
    allowed_domains: A list of domains that this spider is allowed to crawl.
    start_urls: A list of URLs where the spider will begin to crawl from.
    rules: A tuple containing one or more Rule objects. Each Rule defines a certain behavior for crawling the website.
    s3: An AWSS3 object to handle the saving of JSON files to AWS S3 bucket.
    """

    name = "Superside"
    allowed_domains = ["superside.com"]
    start_urls = ["https://www.superside.com"]

    rules = (Rule(callback="parse_item", follow=True),)

    s3 = AWSS3()

    def parse_item(self, response: HtmlResponse) -> None:
        """
        Parses the HTML response of a webpage, stores the URL and HTML content into a JSON file and saves it to an AWS 
        S3 bucket.

        The JSON file is named after the ASCII compliant version of the URL (all non-ASCII characters are replaced 
        with '-').

        Parameters:
            response: An HtmlResponse object representing the response from the crawled webpage.

        Returns:
            None
        """
        page_name = response.url.split("://")[-1].replace("/", "-")
        page_name_cleaned = "".join([i if ord(i) < 128 else "-" for i in page_name])
        file_path = f"pages/{self.name}/{page_name_cleaned}.json"

        item = {
            "url": response.url,
            "content": response.text,
        }

        self.s3.save_dict_to_json(item=item, path=file_path)
