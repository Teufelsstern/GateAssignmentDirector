import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime
import sys


sys.modules['customtkinter'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()


with patch('GateAssignmentDirector.director.GateAssignmentDirector'), \
     patch('GateAssignmentDirector.gad_config.GADConfig.from_yaml'), \
     patch('GateAssignmentDirector.ui.main_window.setup_monitor_tab'), \
     patch('GateAssignmentDirector.ui.main_window.setup_logs_tab'), \
     patch('GateAssignmentDirector.ui.main_window.setup_config_tab'), \
     patch('threading.Thread'):
    from GateAssignmentDirector.ui.main_window import DirectorUI


class TestDirectorUILogMethods(unittest.TestCase):
    """Test suite for DirectorUI log management methods"""

    def setUp(self):
        """Set up test fixtures with mocked UI components"""
        with patch('GateAssignmentDirector.director.GateAssignmentDirector'), \
             patch('GateAssignmentDirector.gad_config.GADConfig.from_yaml'), \
             patch('GateAssignmentDirector.ui.main_window.setup_monitor_tab'), \
             patch('GateAssignmentDirector.ui.main_window.setup_logs_tab'), \
             patch('GateAssignmentDirector.ui.main_window.setup_config_tab'), \
             patch('threading.Thread'), \
             patch.object(DirectorUI, '_update_ui_state'), \
             patch.object(DirectorUI, '_setup_logging'):
            self.ui = DirectorUI()

        self.ui.log_text = MagicMock()
        self.ui.log_text.get = MagicMock()
        self.ui.log_text.configure = MagicMock()
        self.ui.log_text.delete = MagicMock()

    @patch('GateAssignmentDirector.ui.main_window.filedialog.asksaveasfilename')
    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.ui.main_window.datetime')
    def test_save_logs_successful(self, mock_datetime, mock_file, mock_log_info, mock_dialog):
        """Test successful log save operation"""
        mock_datetime.now.return_value.strftime.return_value = "20251001_143000"
        mock_dialog.return_value = "C:/logs/test_log.txt"
        self.ui.log_text.get.return_value = "Test log content\nLine 2\nLine 3"

        self.ui.save_logs()

        mock_dialog.assert_called_once_with(
            defaultextension=".txt",
            initialfile="GAD_log_20251001_143000.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        self.ui.log_text.get.assert_called_once_with("1.0", "end-1c")

        mock_file.assert_called_once_with("C:/logs/test_log.txt", "w", encoding="utf-8")
        mock_file().write.assert_called_once_with("Test log content\nLine 2\nLine 3")

        mock_log_info.assert_called_once_with("Logs saved to C:/logs/test_log.txt")

    @patch('GateAssignmentDirector.ui.main_window.filedialog.asksaveasfilename')
    def test_save_logs_dialog_cancelled(self, mock_dialog):
        """Test save operation when user cancels file dialog"""
        mock_dialog.return_value = ""

        self.ui.save_logs()

        self.ui.log_text.get.assert_not_called()

    @patch('GateAssignmentDirector.ui.main_window.filedialog.asksaveasfilename')
    def test_save_logs_dialog_none(self, mock_dialog):
        """Test save operation when file dialog returns None"""
        mock_dialog.return_value = None

        self.ui.save_logs()

        self.ui.log_text.get.assert_not_called()

    @patch('GateAssignmentDirector.ui.main_window.filedialog.asksaveasfilename')
    @patch('GateAssignmentDirector.ui.main_window.messagebox.showerror')
    @patch('GateAssignmentDirector.ui.main_window.logging.error')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_logs_file_write_error(self, mock_file, mock_log_error, mock_error_box, mock_dialog):
        """Test error handling when file write fails"""
        mock_dialog.return_value = "C:/logs/test_log.txt"
        self.ui.log_text.get.return_value = "Test content"

        write_error = IOError("Permission denied")
        mock_file.return_value.write.side_effect = write_error

        self.ui.save_logs()

        mock_log_error.assert_called_once()
        error_call_args = mock_log_error.call_args[0][0]
        self.assertIn("Failed to save logs", error_call_args)
        self.assertIn("Permission denied", error_call_args)

        mock_error_box.assert_called_once_with(
            "Save Error",
            "Failed to save logs: Permission denied"
        )

    @patch('GateAssignmentDirector.ui.main_window.filedialog.asksaveasfilename')
    @patch('GateAssignmentDirector.ui.main_window.messagebox.showerror')
    @patch('GateAssignmentDirector.ui.main_window.logging.error')
    @patch('builtins.open')
    def test_save_logs_file_open_error(self, mock_file, mock_log_error, mock_error_box, mock_dialog):
        """Test error handling when file cannot be opened"""
        mock_dialog.return_value = "C:/invalid/path/test_log.txt"
        self.ui.log_text.get.return_value = "Test content"

        open_error = FileNotFoundError("No such file or directory")
        mock_file.side_effect = open_error

        self.ui.save_logs()

        mock_log_error.assert_called_once()
        mock_error_box.assert_called_once()

    @patch('GateAssignmentDirector.ui.main_window.filedialog.asksaveasfilename')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_logs_empty_content(self, mock_file, mock_dialog):
        """Test saving logs when log content is empty"""
        mock_dialog.return_value = "C:/logs/empty_log.txt"
        self.ui.log_text.get.return_value = ""

        self.ui.save_logs()

        mock_file().write.assert_called_once_with("")

    @patch('GateAssignmentDirector.ui.main_window.filedialog.asksaveasfilename')
    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.ui.main_window.datetime')
    def test_save_logs_filename_format(self, mock_datetime, mock_file, mock_dialog):
        """Test that default filename uses correct timestamp format"""
        mock_datetime.now.return_value.strftime.return_value = "20251231_235959"
        mock_dialog.return_value = "C:/logs/test.txt"
        self.ui.log_text.get.return_value = "content"

        self.ui.save_logs()

        mock_datetime.now.return_value.strftime.assert_called_once_with("%Y%m%d_%H%M%S")
        call_args = mock_dialog.call_args[1]
        self.assertEqual(call_args['initialfile'], "GAD_log_20251231_235959.txt")

    def test_clear_logs_successful(self):
        """Test successful log clearing operation"""
        self.ui.clear_logs()

        configure_calls = self.ui.log_text.configure.call_args_list
        self.assertEqual(len(configure_calls), 2)
        self.assertEqual(configure_calls[0], unittest.mock.call(state="normal"))
        self.assertEqual(configure_calls[1], unittest.mock.call(state="disabled"))

        self.ui.log_text.delete.assert_called_once_with("1.0", "end")

    def test_clear_logs_state_sequence(self):
        """Test that clear_logs follows correct state enable-delete-disable sequence"""
        call_order = []

        def track_configure(state):
            call_order.append(('configure', state))

        def track_delete(start, end):
            call_order.append(('delete', start, end))

        self.ui.log_text.configure = Mock(side_effect=lambda state: track_configure(state))
        self.ui.log_text.delete = Mock(side_effect=lambda start, end: track_delete(start, end))

        self.ui.clear_logs()

        expected_order = [
            ('configure', 'normal'),
            ('delete', '1.0', 'end'),
            ('configure', 'disabled')
        ]
        self.assertEqual(call_order, expected_order)

    def test_clear_logs_with_exception_during_delete(self):
        """Test that widget state is properly managed even if delete raises exception"""
        self.ui.log_text.delete.side_effect = Exception("Delete failed")

        with self.assertRaises(Exception) as context:
            self.ui.clear_logs()

        self.assertEqual(str(context.exception), "Delete failed")

        configure_calls = self.ui.log_text.configure.call_args_list
        self.assertEqual(configure_calls[0], unittest.mock.call(state="normal"))

    def test_clear_logs_widget_remains_disabled(self):
        """Test that log_text widget ends in disabled state after clearing"""
        self.ui.clear_logs()

        final_call = self.ui.log_text.configure.call_args_list[-1]
        self.assertEqual(final_call, unittest.mock.call(state="disabled"))


class TestDirectorUIMonitoringControls(unittest.TestCase):
    """Test suite for DirectorUI monitoring control methods"""

    def setUp(self):
        """Set up test fixtures with mocked UI components"""
        with patch('GateAssignmentDirector.director.GateAssignmentDirector') as mock_director_cls, \
             patch('GateAssignmentDirector.gad_config.GADConfig.from_yaml'), \
             patch('GateAssignmentDirector.ui.main_window.setup_monitor_tab'), \
             patch('GateAssignmentDirector.ui.main_window.setup_logs_tab'), \
             patch('GateAssignmentDirector.ui.main_window.setup_config_tab'), \
             patch('threading.Thread'), \
             patch.object(DirectorUI, '_update_ui_state'), \
             patch.object(DirectorUI, '_setup_logging'):
            self.ui = DirectorUI()

        self.ui.director = MagicMock()
        self.ui.start_btn = MagicMock()
        self.ui.stop_btn = MagicMock()
        self.ui.status_label = MagicMock()
        self.ui.activity_text = MagicMock()
        self.ui.airport_label = MagicMock()
        self.ui.config = MagicMock()
        self.ui.config.flight_json_path = "C:/test/flight.json"

    @patch('threading.Timer')
    def test_start_monitoring_ui_state_changes(self, mock_timer):
        """Test start_monitoring updates UI state correctly"""
        self.ui.start_monitoring()

        self.ui.start_btn.configure.assert_called_once_with(state="disabled")
        self.ui.stop_btn.configure.assert_called_once_with(state="normal", text_color="#4a4050")
        self.ui.status_label.configure.assert_called_once_with(text="Monitoring", text_color="#9dc4a8")

    @patch('threading.Timer')
    def test_start_monitoring_activity_log_entry(self, mock_timer):
        """Test start_monitoring adds activity log entry"""
        self.ui.start_monitoring()

        self.ui.activity_text.insert.assert_called_once_with("end", "Starting monitoring...\n")
        mock_timer.assert_called_once_with(0.5, self.ui._continue_monitoring_startup)
        mock_timer.return_value.start.assert_called_once()

    @patch('threading.Thread')
    @patch('threading.Timer')
    def test_start_monitoring_spawns_thread(self, mock_timer, mock_thread):
        """Test start_monitoring creates daemon thread for director"""
        # Capture the timer callback and invoke it immediately
        def execute_callback(delay, callback):
            callback()
            return MagicMock()

        mock_timer.side_effect = execute_callback

        self.ui.start_monitoring()

        mock_thread.assert_called_once()
        call_kwargs = mock_thread.call_args[1]
        self.assertEqual(call_kwargs['target'], self.ui._run_director)
        self.assertTrue(call_kwargs['daemon'])
        mock_thread.return_value.start.assert_called_once()

    def test_stop_monitoring_ui_state_changes(self):
        """Test stop_monitoring updates UI state correctly"""
        self.ui.stop_monitoring()

        self.ui.start_btn.configure.assert_called_once_with(state="normal")
        self.ui.stop_btn.configure.assert_called_once_with(state="disabled", text_color="#e8d9d6")
        self.ui.status_label.configure.assert_called_once_with(text="Stopped", text_color="#C67B7B")

    def test_stop_monitoring_calls_director_stop(self):
        """Test stop_monitoring invokes director.stop()"""
        self.ui.stop_monitoring()

        self.ui.director.stop.assert_called_once()

    def test_stop_monitoring_activity_log_entry(self):
        """Test stop_monitoring adds activity log entry"""
        self.ui.stop_monitoring()

        self.ui.activity_text.insert.assert_called_once_with("end", "Monitoring stopped.\n")

    @patch('GateAssignmentDirector.ui.main_window.logging.error')
    def test_run_director_calls_director_methods(self, mock_log_error):
        """Test _run_director invokes director start and process methods"""
        self.ui._run_director()

        self.ui.director.start_monitoring.assert_called_once_with("C:/test/flight.json")
        self.ui.director.process_gate_assignments.assert_called_once()

    @patch('GateAssignmentDirector.ui.main_window.logging.error')
    def test_run_director_handles_exceptions(self, mock_log_error):
        """Test _run_director logs errors when director raises exception"""
        error = RuntimeError("SimConnect failed")
        self.ui.director.start_monitoring.side_effect = error

        self.ui._run_director()

        mock_log_error.assert_called_once()
        error_msg = mock_log_error.call_args[0][0]
        self.assertIn("Director error", error_msg)
        self.assertIn("SimConnect failed", error_msg)


class TestDirectorUIOverrideControls(unittest.TestCase):
    """Test suite for DirectorUI manual override control methods"""

    def setUp(self):
        """Set up test fixtures with mocked UI components"""
        with patch('GateAssignmentDirector.director.GateAssignmentDirector'), \
             patch('GateAssignmentDirector.gad_config.GADConfig.from_yaml'), \
             patch('GateAssignmentDirector.ui.main_window.setup_monitor_tab'), \
             patch('GateAssignmentDirector.ui.main_window.setup_logs_tab'), \
             patch('GateAssignmentDirector.ui.main_window.setup_config_tab'), \
             patch('threading.Thread'), \
             patch.object(DirectorUI, '_update_ui_state'), \
             patch.object(DirectorUI, '_setup_logging'):
            self.ui = DirectorUI()

        self.ui.override_airport_entry = MagicMock()
        self.ui.override_terminal_entry = MagicMock()
        self.ui.override_gate_entry = MagicMock()
        self.ui.airport_label = MagicMock()
        self.ui.activity_text = MagicMock()
        self.ui.override_panel = MagicMock()
        self.ui.override_toggle_btn = MagicMock()
        self.ui.root = MagicMock()

    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    def test_apply_override_successful(self, mock_log_info):
        """Test apply_override with valid airport data"""
        self.ui.override_airport_entry.get.return_value = "EDDF"
        self.ui.override_terminal_entry.get.return_value = "1"
        self.ui.override_gate_entry.get.return_value = "A23"

        self.ui.apply_override()

        self.assertTrue(self.ui.override_active)
        self.assertEqual(self.ui.override_airport, "EDDF")
        self.assertEqual(self.ui.override_terminal, "1")
        self.assertEqual(self.ui.override_gate, "A23")
        self.assertEqual(self.ui.current_airport, "EDDF")

        self.ui.airport_label.configure.assert_called_once_with(
            text="EDDF (MANUAL)",
            text_color="#D4A574"
        )

        self.ui.activity_text.insert.assert_called_once()
        activity_msg = self.ui.activity_text.insert.call_args[0][1]
        self.assertIn("Manual override applied", activity_msg)
        self.assertIn("EDDF", activity_msg)

        mock_log_info.assert_called_once()

    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    def test_apply_override_with_whitespace(self, mock_log_info):
        """Test apply_override strips whitespace from inputs"""
        self.ui.override_airport_entry.get.return_value = "  KJFK  "
        self.ui.override_terminal_entry.get.return_value = "  4  "
        self.ui.override_gate_entry.get.return_value = "  B32  "

        self.ui.apply_override()

        self.assertEqual(self.ui.override_airport, "KJFK")
        self.assertEqual(self.ui.override_terminal, "4")
        self.assertEqual(self.ui.override_gate, "B32")

    @patch('GateAssignmentDirector.ui.main_window.messagebox.showwarning')
    def test_apply_override_missing_airport(self, mock_warning):
        """Test apply_override shows warning when airport is empty"""
        self.ui.override_airport_entry.get.return_value = ""
        self.ui.override_terminal_entry.get.return_value = "1"
        self.ui.override_gate_entry.get.return_value = "A10"

        self.ui.apply_override()

        mock_warning.assert_called_once_with("Missing Data", "Airport is required for override.")
        self.assertFalse(self.ui.override_active)

    @patch('GateAssignmentDirector.ui.main_window.messagebox.showwarning')
    def test_apply_override_whitespace_only_airport(self, mock_warning):
        """Test apply_override treats whitespace-only airport as empty"""
        self.ui.override_airport_entry.get.return_value = "   "
        self.ui.override_terminal_entry.get.return_value = "1"
        self.ui.override_gate_entry.get.return_value = "A10"

        self.ui.apply_override()

        mock_warning.assert_called_once()
        self.assertFalse(self.ui.override_active)

    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    def test_apply_override_empty_terminal_and_gate(self, mock_log_info):
        """Test apply_override allows empty terminal and gate"""
        self.ui.override_airport_entry.get.return_value = "LFPG"
        self.ui.override_terminal_entry.get.return_value = ""
        self.ui.override_gate_entry.get.return_value = ""

        self.ui.apply_override()

        self.assertTrue(self.ui.override_active)
        self.assertEqual(self.ui.override_airport, "LFPG")
        self.assertEqual(self.ui.override_terminal, "")
        self.assertEqual(self.ui.override_gate, "")

    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    def test_clear_override_resets_state(self, mock_log_info):
        """Test clear_override resets all override state"""
        self.ui.override_active = True
        self.ui.override_airport = "EDDF"
        self.ui.override_terminal = "1"
        self.ui.override_gate = "A23"
        self.ui.director.current_airport = "KJFK"

        self.ui.clear_override()

        self.assertFalse(self.ui.override_active)
        self.assertIsNone(self.ui.override_airport)
        self.assertIsNone(self.ui.override_terminal)
        self.assertIsNone(self.ui.override_gate)
        self.assertEqual(self.ui.current_airport, "KJFK")

    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    def test_clear_override_clears_entry_fields(self, mock_log_info):
        """Test clear_override clears all entry widgets"""
        self.ui.clear_override()

        self.ui.override_airport_entry.delete.assert_called_once_with(0, "end")
        self.ui.override_terminal_entry.delete.assert_called_once_with(0, "end")
        self.ui.override_gate_entry.delete.assert_called_once_with(0, "end")

    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    def test_clear_override_activity_log_entry(self, mock_log_info):
        """Test clear_override adds activity log entry"""
        self.ui.clear_override()

        self.ui.activity_text.insert.assert_called_once_with("end", "Manual override cleared.\n")
        mock_log_info.assert_called_once_with("Manual override cleared")

    def test_toggle_override_section_shows_panel(self):
        """Test toggle_override_section makes panel visible"""
        self.ui.override_section_visible = False

        self.ui.toggle_override_section()

        self.ui.override_panel.pack.assert_called_once_with(fill="x", pady=(5, 0))
        self.ui.override_toggle_btn.configure.assert_called_once_with(text="▲ Manual Override")
        self.ui.root.minsize.assert_called_once_with(470, 500)
        self.assertTrue(self.ui.override_section_visible)

    def test_toggle_override_section_hides_panel(self):
        """Test toggle_override_section hides visible panel"""
        self.ui.override_section_visible = True

        self.ui.toggle_override_section()

        self.ui.override_panel.pack_forget.assert_called_once()
        self.ui.override_toggle_btn.configure.assert_called_once_with(text="▼ Manual Override")
        self.ui.root.minsize.assert_called_once_with(350, 430)
        self.assertFalse(self.ui.override_section_visible)


class TestDirectorUIGateManagement(unittest.TestCase):
    """Test suite for DirectorUI gate management methods"""

    def setUp(self):
        """Set up test fixtures with mocked UI components"""
        with patch('GateAssignmentDirector.director.GateAssignmentDirector'), \
             patch('GateAssignmentDirector.gad_config.GADConfig.from_yaml'), \
             patch('GateAssignmentDirector.ui.main_window.setup_monitor_tab'), \
             patch('GateAssignmentDirector.ui.main_window.setup_logs_tab'), \
             patch('GateAssignmentDirector.ui.main_window.setup_config_tab'), \
             patch('threading.Thread'), \
             patch.object(DirectorUI, '_update_ui_state'), \
             patch.object(DirectorUI, '_setup_logging'):
            self.ui = DirectorUI()

        self.ui.activity_text = MagicMock()
        self.ui.root = MagicMock()

    @patch('GateAssignmentDirector.ui.main_window.GateManagementWindow')
    def test_edit_gates_with_current_airport(self, mock_gate_window):
        """Test edit_gates opens window with current airport"""
        self.ui.current_airport = "EDDF"

        self.ui.edit_gates()

        mock_gate_window.assert_called_once_with(self.ui.root, "EDDF")

    @patch('GateAssignmentDirector.ui.main_window.GateManagementWindow')
    @patch('GateAssignmentDirector.ui.main_window.messagebox.showwarning')
    def test_edit_gates_without_current_airport(self, mock_warning, mock_gate_window):
        """Test edit_gates shows warning when no airport detected"""
        self.ui.current_airport = None

        self.ui.edit_gates()

        mock_warning.assert_called_once()
        warning_msg = mock_warning.call_args[0][1]
        self.assertIn("No airport has been detected", warning_msg)

        mock_gate_window.assert_called_once_with(self.ui.root, None)

    @patch('GateAssignmentDirector.ui.main_window.messagebox.showerror')
    def test_assign_gate_manual_no_airport(self, mock_error):
        """Test assign_gate_manual shows error when no airport data available"""
        self.ui.current_airport = None

        self.ui.assign_gate_manual()

        mock_error.assert_called_once_with("Error", "No airport data available. Set manual override or start monitoring.")

    @patch('GateAssignmentDirector.ui.main_window.messagebox.showwarning')
    def test_assign_gate_manual_override_without_gate(self, mock_warning):
        """Test assign_gate_manual shows warning when override has no gate"""
        self.ui.current_airport = "EDDF"
        self.ui.override_active = True
        self.ui.override_airport = "EDDF"
        self.ui.override_terminal = "1"
        self.ui.override_gate = ""

        self.ui.assign_gate_manual()

        mock_warning.assert_called_once_with("Missing Gate", "No gate information available. Please set manual override with gate details.")

    @patch('threading.Thread')
    @patch('GateAssignmentDirector.ui.main_window.GsxHook')
    def test_assign_gate_manual_with_override(self, mock_gsx_hook, mock_thread):
        """Test assign_gate_manual with override active"""
        self.ui.current_airport = "EDDF"
        self.ui.override_active = True
        self.ui.override_airport = "EDDF"
        self.ui.override_terminal = "1"
        self.ui.override_gate = "A23"

        mock_gsx = MagicMock()
        mock_gsx.is_initialized = True
        self.ui.director.gsx = mock_gsx

        self.ui.assign_gate_manual()

        self.ui.activity_text.insert.assert_called_once()
        activity_msg = self.ui.activity_text.insert.call_args[0][1]
        self.assertIn("Assigning gate", activity_msg)
        self.assertIn("EDDF", activity_msg)
        self.assertIn("A23", activity_msg)

        mock_thread.assert_called_once()
        thread_kwargs = mock_thread.call_args[1]
        self.assertEqual(thread_kwargs['target'], self.ui._assign_gate_thread)
        self.assertEqual(thread_kwargs['args'], ("EDDF", "1", "A23"))
        self.assertTrue(thread_kwargs['daemon'])

    @patch('threading.Thread')
    @patch('GateAssignmentDirector.ui.main_window.GsxHook')
    def test_assign_gate_manual_initializes_gsx_when_needed(self, mock_gsx_hook_cls, mock_thread):
        """Test assign_gate_manual initializes GSX if not initialized"""
        self.ui.current_airport = "EDDF"
        self.ui.override_active = True
        self.ui.override_airport = "EDDF"
        self.ui.override_terminal = "1"
        self.ui.override_gate = "A23"

        self.ui.director.gsx = None
        mock_gsx = MagicMock()
        mock_gsx.is_initialized = True
        mock_gsx_hook_cls.return_value = mock_gsx

        self.ui.assign_gate_manual()

        mock_gsx_hook_cls.assert_called_once_with(self.ui.director.config, enable_menu_logging=True)
        self.assertEqual(self.ui.director.gsx, mock_gsx)

    @patch('threading.Thread')
    @patch('GateAssignmentDirector.ui.main_window.GsxHook')
    @patch('GateAssignmentDirector.ui.main_window.messagebox.showerror')
    def test_assign_gate_manual_gsx_initialization_failure(self, mock_error, mock_gsx_hook_cls, mock_thread):
        """Test assign_gate_manual shows error when GSX initialization fails"""
        self.ui.current_airport = "EDDF"
        self.ui.override_active = True
        self.ui.override_airport = "EDDF"
        self.ui.override_terminal = "1"
        self.ui.override_gate = "A23"

        self.ui.director.gsx = None
        mock_gsx = MagicMock()
        mock_gsx.is_initialized = False
        mock_gsx_hook_cls.return_value = mock_gsx

        self.ui.assign_gate_manual()

        mock_error.assert_called_once_with("Error", "Failed to initialize GSX Hook")
        mock_thread.assert_not_called()

    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    def test_assign_gate_thread_successful(self, mock_log_info):
        """Test _assign_gate_thread with successful gate assignment"""
        mock_gsx = MagicMock()
        mock_gsx.assign_gate_when_ready.return_value = (True, {'gate': 'A23'})
        self.ui.director.gsx = mock_gsx

        self.ui._assign_gate_thread("EDDF", "1", "A23")

        mock_gsx.assign_gate_when_ready.assert_called_once_with(
            airport="EDDF",
            terminal="1",
            gate_number="A23",
            wait_for_ground=True
        )

        self.ui.activity_text.after.assert_called_once()
        after_call = self.ui.activity_text.after.call_args
        self.assertEqual(after_call[0][0], 0)
        after_lambda = after_call[0][1]
        after_lambda()
        insert_call = self.ui.activity_text.insert.call_args[0][1]
        self.assertIn("Successfully assigned to gate: A23", insert_call)

        mock_log_info.assert_called_once()
        log_msg = mock_log_info.call_args[0][0]
        self.assertIn("Manual gate assignment succeeded: A23", log_msg)

    @patch('GateAssignmentDirector.ui.main_window.logging.info')
    def test_assign_gate_thread_failed(self, mock_log_info):
        """Test _assign_gate_thread with failed gate assignment"""
        mock_gsx = MagicMock()
        mock_gsx.assign_gate_when_ready.return_value = (False, None)
        self.ui.director.gsx = mock_gsx

        self.ui._assign_gate_thread("EDDF", "1", "A23")

        after_call = self.ui.activity_text.after.call_args
        after_lambda = after_call[0][1]
        after_lambda()
        insert_call = self.ui.activity_text.insert.call_args[0][1]
        self.assertIn("failed", insert_call)

    @patch('GateAssignmentDirector.ui.main_window.logging.error')
    def test_assign_gate_thread_exception(self, mock_log_error):
        """Test _assign_gate_thread handles exceptions"""
        mock_gsx = MagicMock()
        mock_gsx.assign_gate_when_ready.side_effect = RuntimeError("GSX error")
        self.ui.director.gsx = mock_gsx

        self.ui._assign_gate_thread("EDDF", "1", "A23")

        mock_log_error.assert_called_once()
        error_msg = mock_log_error.call_args[0][0]
        self.assertIn("Gate assignment error", error_msg)
        self.assertIn("GSX error", error_msg)

        after_call = self.ui.activity_text.after.call_args
        after_lambda = after_call[0][1]
        after_lambda()
        insert_call = self.ui.activity_text.insert.call_args[0][1]
        self.assertIn("Gate assignment error", insert_call)


if __name__ == '__main__':
    unittest.main()
