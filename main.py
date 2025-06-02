#!/usr/bin/env python3
"""
Facebook Groups Post Automation Tool
Main application entry point
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ui.main_window import MainWindow
from core.post_scheduler import PostScheduler
from utils.file_manager import FileManager

def setup_logging():
    # Set up logging with UTF-8 encoding
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('automation.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
)

def main():
    """Main application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create data directories if they don't exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Initialize Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Facebook Groups Automation")
    app.setOrganizationName("FB Automation Tool")
    
    # Initialize core components
    file_manager = FileManager()
    scheduler = PostScheduler()
    
    # Create main window
    main_window = MainWindow(scheduler, file_manager)
    main_window.show()
    
    # Setup scheduler timer
    timer = QTimer()
    timer.timeout.connect(scheduler.check_scheduled_posts)
    timer.start(30000)  # Check every minute
    
    logger.info("Facebook Groups Automation Tool started")
    
    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
