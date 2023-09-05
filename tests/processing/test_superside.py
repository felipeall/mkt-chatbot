from unittest.mock import MagicMock, patch

import pytest

from processing._base import BaseProcessing
from processing.superside import Superside


@pytest.fixture
def mock_base_processing():
    with patch.object(BaseProcessing, "__init__", return_value=None):
        yield


@pytest.fixture
def mock_superside(mock_base_processing):
    with patch.object(Superside, "__post_init__"):
        yield Superside(company="Superside", full_load=False, debug=False)


def test_run(mock_superside):
    mock_superside.s3 = MagicMock()
    mock_superside.s3.list_files_from_path = MagicMock(return_value=["test1.json"])
    mock_superside.s3.read_json = MagicMock(
        return_value={"content": "<div><p>Test content</p></div>", "url": "http://test.url"},
    )
    mock_superside.extract_text_by_xpath = MagicMock(return_value="Test content")

    mock_collection = MagicMock()
    mock_superside.collection = mock_collection

    mock_superside.run()
    assert mock_collection.replace_one.called
