import unittest
from unittest.mock import Mock, patch, mock_open
import time
from GateAssignmentDirector.tooltip_reader import TooltipReader


class TestTooltipReader(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock()
        self.mock_config.tooltip_file_paths = [
            "C:\\test\\path1\\tooltip",
            "C:\\test\\path2\\tooltip"
        ]
        self.mock_config.tooltip_success_keyphrases = [
            "marshaller has been dispatched",
            "follow me car",
            "boarding"
        ]
        self.reader = TooltipReader(self.mock_config)

    def test_init_with_config(self):
        """Test initialization with config"""
        self.assertEqual(self.reader.tooltip_paths, self.mock_config.tooltip_file_paths)
        self.assertEqual(self.reader.success_keyphrases, self.mock_config.tooltip_success_keyphrases)

    def test_init_with_none_paths(self):
        """Test initialization when tooltip_file_paths is None"""
        config = Mock()
        config.tooltip_file_paths = None
        config.tooltip_success_keyphrases = ["test"]

        reader = TooltipReader(config)
        self.assertEqual(reader.tooltip_paths, [])

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    def test_get_file_timestamp_single_file(self, mock_getmtime, mock_exists):
        """Test getting timestamp from single existing file"""
        mock_exists.side_effect = lambda path: path == "C:\\test\\path1\\tooltip"
        mock_getmtime.return_value = 1234567890.0

        timestamp = self.reader.get_file_timestamp()

        self.assertEqual(timestamp, 1234567890.0)
        mock_getmtime.assert_called_once_with("C:\\test\\path1\\tooltip")

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    def test_get_file_timestamp_multiple_files(self, mock_getmtime, mock_exists):
        """Test getting most recent timestamp from multiple files"""
        mock_exists.return_value = True
        mock_getmtime.side_effect = [1234567890.0, 1234567900.0]  # Second file is newer

        timestamp = self.reader.get_file_timestamp()

        self.assertEqual(timestamp, 1234567900.0)  # Should return newer timestamp

    @patch('os.path.exists')
    def test_get_file_timestamp_no_files_exist(self, mock_exists):
        """Test getting timestamp when no files exist"""
        mock_exists.return_value = False

        timestamp = self.reader.get_file_timestamp()

        self.assertIsNone(timestamp)

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    def test_get_file_timestamp_with_error(self, mock_getmtime, mock_exists):
        """Test getting timestamp handles OSError gracefully"""
        mock_exists.return_value = True
        mock_getmtime.side_effect = OSError("Permission denied")

        timestamp = self.reader.get_file_timestamp()

        self.assertIsNone(timestamp)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="[GSX] A marshaller has been dispatched on site")
    def test_read_tooltip_success(self, mock_file, mock_exists):
        """Test reading tooltip content"""
        mock_exists.side_effect = lambda path: path == "C:\\test\\path1\\tooltip"

        content = self.reader.read_tooltip()

        self.assertEqual(content, "[GSX] A marshaller has been dispatched on site")
        mock_file.assert_called_once_with("C:\\test\\path1\\tooltip", "r", encoding="utf-8")

    @patch('os.path.exists')
    def test_read_tooltip_no_files_exist(self, mock_exists):
        """Test reading tooltip when no files exist"""
        mock_exists.return_value = False

        content = self.reader.read_tooltip()

        self.assertEqual(content, "")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_read_tooltip_with_error(self, mock_file, mock_exists):
        """Test reading tooltip handles OSError gracefully"""
        mock_exists.return_value = True
        mock_file.side_effect = OSError("Permission denied")

        content = self.reader.read_tooltip()

        self.assertEqual(content, "")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="[GSX] Follow me car")
    def test_read_tooltip_uses_first_existing_file(self, mock_file, mock_exists):
        """Test that read_tooltip uses first existing file"""
        mock_exists.side_effect = lambda path: path == "C:\\test\\path2\\tooltip"

        content = self.reader.read_tooltip()

        # Should skip path1 and read from path2
        mock_file.assert_called_once_with("C:\\test\\path2\\tooltip", "r", encoding="utf-8")

    @patch.object(TooltipReader, 'get_file_timestamp')
    @patch.object(TooltipReader, 'read_tooltip')
    def test_check_for_success_immediate_match(self, mock_read, mock_timestamp):
        """Test check_for_success when tooltip immediately confirms"""
        mock_timestamp.side_effect = [1000.0, 1001.0]  # Timestamp changed
        mock_read.return_value = "[GSX] A marshaller has been dispatched on site"

        result = self.reader.check_for_success(baseline_timestamp=1000.0, timeout=2.0)

        self.assertTrue(result)

    @patch.object(TooltipReader, 'get_file_timestamp')
    @patch.object(TooltipReader, 'read_tooltip')
    def test_check_for_success_case_insensitive(self, mock_read, mock_timestamp):
        """Test check_for_success is case insensitive"""
        mock_timestamp.side_effect = [1000.0, 1001.0]
        mock_read.return_value = "[GSX] A MARSHALLER HAS BEEN DISPATCHED on site"

        result = self.reader.check_for_success(baseline_timestamp=1000.0, timeout=2.0)

        self.assertTrue(result)

    @patch.object(TooltipReader, 'get_file_timestamp')
    @patch.object(TooltipReader, 'read_tooltip')
    @patch('time.sleep')
    def test_check_for_success_timestamp_unchanged(self, mock_sleep, mock_read, mock_timestamp):
        """Test check_for_success times out when timestamp doesn't change"""
        mock_timestamp.return_value = 1000.0  # Timestamp never changes
        mock_read.return_value = "[GSX] A marshaller has been dispatched"

        result = self.reader.check_for_success(baseline_timestamp=1000.0, timeout=0.5, check_interval=0.1)

        self.assertFalse(result)

    @patch.object(TooltipReader, 'get_file_timestamp')
    @patch.object(TooltipReader, 'read_tooltip')
    @patch('time.sleep')
    def test_check_for_success_no_keyphrase_match(self, mock_sleep, mock_read, mock_timestamp):
        """Test check_for_success fails when no keyphrase matches"""
        mock_timestamp.return_value = 1001.0  # Timestamp changed
        mock_read.return_value = "[GSX] Some other message"

        result = self.reader.check_for_success(baseline_timestamp=1000.0, timeout=0.5, check_interval=0.1)

        self.assertFalse(result)

    @patch.object(TooltipReader, 'get_file_timestamp')
    def test_check_for_success_no_paths_configured(self, mock_timestamp):
        """Test check_for_success returns False when no paths configured"""
        self.reader.tooltip_paths = []

        result = self.reader.check_for_success(baseline_timestamp=1000.0)

        self.assertFalse(result)
        mock_timestamp.assert_not_called()

    @patch.object(TooltipReader, 'get_file_timestamp')
    def test_check_for_success_no_keyphrases_configured(self, mock_timestamp):
        """Test check_for_success returns False when no keyphrases configured"""
        self.reader.success_keyphrases = []

        result = self.reader.check_for_success(baseline_timestamp=1000.0)

        self.assertFalse(result)
        mock_timestamp.assert_not_called()

    @patch.object(TooltipReader, 'get_file_timestamp')
    @patch.object(TooltipReader, 'read_tooltip')
    def test_check_for_success_baseline_none(self, mock_read, mock_timestamp):
        """Test check_for_success when baseline is None (file didn't exist initially)"""
        mock_timestamp.return_value = 1001.0  # File now exists
        mock_read.return_value = "[GSX] Boarding has started"

        result = self.reader.check_for_success(baseline_timestamp=None, timeout=2.0)

        self.assertTrue(result)

    @patch.object(TooltipReader, 'get_file_timestamp')
    @patch.object(TooltipReader, 'read_tooltip')
    def test_check_for_success_multiple_keyphrases(self, mock_read, mock_timestamp):
        """Test check_for_success matches any configured keyphrase"""
        mock_timestamp.side_effect = [1000.0, 1001.0]
        mock_read.return_value = "[GSX] Boarding has started"  # Matches "boarding"

        result = self.reader.check_for_success(baseline_timestamp=1000.0, timeout=2.0)

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
