import sys
import unittest
from unittest.mock import MagicMock, patch
import os

# Force mock tkinter modules
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.simpledialog'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()

# Now import the GUI module which will use the mocks
import pysipp_gui

class TestSippGUI(unittest.TestCase):
    def setUp(self):
        # We need to patch Tk and other widgets inside the class instantiation if needed
        # But since we mocked the module, SippGUI(root) should work with mocks
        self.root = MagicMock()
        self.gui = pysipp_gui.SippGUI(self.root)
        # Mock the log method to capture output for assertions
        self.gui.log = MagicMock()
        # Mock the execute_pysipp to NOT run in thread for some tests if we want synchronous testing
        # But here we want to test execute_pysipp logic itself.

    @patch('pysipp.client')
    def test_run_client(self, mock_client):
        # Create a mock for the client instance returned by pysipp.client(...)
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        # The GUI accesses .cmd attribute for logging
        mock_instance.cmd = "mock_client_cmd"

        # Call the method directly (bypassing threading if we call execute_pysipp)
        self.gui.execute_pysipp("client 127.0.0.1 5060")

        # Verify pysipp.client was called with correct args
        mock_client.assert_called_with(destaddr=('127.0.0.1', 5060))
        # Verify the client instance was called (executed)
        mock_instance.assert_called_once()
        # Verify success log
        self.gui.log.assert_any_call("Client execution finished.")

    @patch('pysipp.server')
    def test_run_server(self, mock_server):
        mock_instance = MagicMock()
        mock_server.return_value = mock_instance
        mock_instance.cmd = "mock_server_cmd"

        self.gui.execute_pysipp("server 127.0.0.1 5060")

        mock_server.assert_called_with(srcaddr=('127.0.0.1', 5060))
        mock_instance.assert_called_once()
        self.gui.log.assert_any_call("Server execution finished.")

    @patch('pysipp.scenario')
    def test_run_scenario(self, mock_scenario):
        mock_instance = MagicMock()
        mock_scenario.return_value = mock_instance
        mock_instance.cmd = "mock_scen_cmd"

        self.gui.execute_pysipp("scenario /path/to/scenario")

        mock_scenario.assert_called_with(dirpath='/path/to/scenario')
        mock_instance.assert_called_once()
        self.gui.log.assert_any_call("Scenario execution finished.")

    def test_invalid_command(self):
        self.gui.execute_pysipp("foo bar")
        # Check that it logged "Unknown command"
        # Since log is mocked, we check calls
        # args[0] of the call should contain "Unknown command"
        found = False
        for call in self.gui.log.call_args_list:
            if "Unknown command: foo" in str(call):
                found = True
                break
        self.assertTrue(found, "Did not find unknown command log")

    def test_client_invalid_args(self):
        self.gui.execute_pysipp("client 127.0.0.1")
        self.gui.log.assert_any_call("Usage: client <dest_ip> <dest_port>")

if __name__ == '__main__':
    unittest.main()
