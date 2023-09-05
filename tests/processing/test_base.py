from unittest.mock import MagicMock

from lxml.html import HtmlElement
from pymongo.collection import Collection

from processing._base import BaseProcessing


def test_get_files_paths(mocker):
    mocker.patch("processing._base.glob", return_value=["file1", "file2", "file3"])
    bp = BaseProcessing("Test", False, False)
    assert bp.get_files_paths() == ["file1", "file2", "file3"]


def test_extract_next_data(mocker):
    bp = BaseProcessing("Test", False, False)
    html_element = HtmlElement()
    mocker.patch.object(html_element, "xpath", return_value=['{"paragraph": "Test paragraph"}'])
    mocker.patch.object(bp, "cleanhtml", return_value="Test paragraph")
    assert bp.extract_next_data(html_element) == "Test paragraph"


def test_extract_text_by_xpath(mocker):
    html_element = HtmlElement()
    mocker.patch.object(html_element, "xpath", return_value=["Test text"])
    bp = BaseProcessing("Test", False, False)
    assert bp.extract_text_by_xpath(html_element, "//div") == "Test text"


def test_cleanhtml(mocker):
    bp = BaseProcessing("Test", False, False)
    text = "<div>Test</div>"
    cleaned_text = bp.cleanhtml(text)
    assert cleaned_text == "Test"


def test_connect_mongodb(mocker):
    bp = BaseProcessing("Test", False, False)
    mocker.patch("pymongo.MongoClient", return_value=MagicMock())
    bp._connect_mongodb()
    assert isinstance(bp.collection, Collection)


def test_set_logger_level(mocker):
    bp = BaseProcessing("Test", False, False)
    mocker.patch("processing._base.logger")
    bp._set_logger_level()
    bp.log.add.assert_called()
