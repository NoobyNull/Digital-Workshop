#!/usr/bin/env python3
"""
Sample Large Module - Over 500 lines
This module demonstrates a monolithic architecture pattern that should be flagged.
"""

import os
import sys
import json
import csv
import sqlite3
import logging
import datetime
import hashlib
import re
import math
import random
from typing import List, Dict, Optional, Union, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import time
import functools
import itertools
from urllib.parse import urlparse, parse_qs
import base64
import zlib
import pickle


@dataclass
class Config:
    """Configuration settings."""
    debug: bool = False
    max_workers: int = 4
    batch_size: int = 1000
    timeout: int = 30
    retry_count: int = 3


class DatabaseManager:
    """Database management operations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    def connect(self):
        """Connect to database."""
        self.connection = sqlite3.connect(self.db_path)
    
    def disconnect(self):
        """Disconnect from database."""
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute SQL query."""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    
    def create_tables(self):
        """Create database tables."""
        queries = [
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)",
            "CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL)",
            "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, quantity INTEGER)"
        ]
        for query in queries:
            self.execute_query(query)


class FileProcessor:
    """File processing operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def read_file(self, filepath: str) -> str:
        """Read file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {filepath}: {e}")
            return ""
    
    def write_file(self, filepath: str, content: str) -> bool:
        """Write content to file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Error writing file {filepath}: {e}")
            return False
    
    def process_csv(self, csv_path: str) -> List[Dict]:
        """Process CSV file."""
        results = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results.append(row)
        except Exception as e:
            self.logger.error(f"Error processing CSV {csv_path}: {e}")
        return results
    
    def process_json(self, json_path: str) -> Dict:
        """Process JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error processing JSON {json_path}: {e}")
            return {}


class DataValidator:
    """Data validation operations."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number."""
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate date format."""
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except:
            return False
    
    @staticmethod
    def validate_number(value: str) -> bool:
        """Validate numeric value."""
        try:
            float(value)
            return True
        except:
            return False


class DataTransformer:
    """Data transformation operations."""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Convert to lowercase
        text = text.lower()
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()
    
    @staticmethod
    def encode_data(data: str) -> str:
        """Encode data using base64."""
        return base64.b64encode(data.encode()).decode()
    
    @staticmethod
    def compress_data(data: str) -> bytes:
        """Compress data using zlib."""
        return zlib.compress(data.encode())
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Hash data using SHA256."""
        return hashlib.sha256(data.encode()).hexdigest()


class ReportGenerator:
    """Report generation operations."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def generate_summary_report(self, data: List[Dict]) -> str:
        """Generate summary report."""
        total_records = len(data)
        unique_users = len(set(record.get('user_id', '') for record in data))
        total_amount = sum(float(record.get('amount', 0)) for record in data)
        
        report = f"""
        Summary Report
        ==============
        Total Records: {total_records}
        Unique Users: {unique_users}
        Total Amount: ${total_amount:.2f}
        Generated: {datetime.datetime.now()}
        """
        return report
    
    def generate_detailed_report(self, data: List[Dict]) -> str:
        """Generate detailed report."""
        report = "Detailed Report\n" + "=" * 50 + "\n"
        
        for i, record in enumerate(data, 1):
            report += f"\nRecord {i}:\n"
            for key, value in record.items():
                report += f"  {key}: {value}\n"
        
        return report
    
    def export_to_csv(self, data: List[Dict], filepath: str) -> bool:
        """Export data to CSV."""
        try:
            if not data:
                return False
            
            fieldnames = data[0].keys()
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            return True
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            return False


class CacheManager:
    """Cache management operations."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            if time.time() < self.cache_ttl.get(key, 0):
                return self.cache[key]
            else:
                del self.cache[key]
                del self.cache_ttl[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache."""
        self.cache[key] = value
        self.cache_ttl[key] = time.time() + ttl
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        self.cache_ttl.clear()


class APIClient:
    """API client operations."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
    
    def make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
        """Make API request."""
        # This is a simplified implementation
        url = f"{self.base_url}/{endpoint}"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        # Simulate API call
        time.sleep(0.1)  # Simulate network delay
        
        return {
            'status': 'success',
            'data': {'message': 'API call completed'},
            'timestamp': datetime.datetime.now().isoformat()
        }


class NotificationService:
    """Notification service operations."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email notification."""
        # Simulate email sending
        logging.info(f"Email sent to {to}: {subject}")
        return True
    
    def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS notification."""
        # Simulate SMS sending
        logging.info(f"SMS sent to {phone}: {message}")
        return True
    
    def send_webhook(self, url: str, data: Dict) -> bool:
        """Send webhook notification."""
        # Simulate webhook call
        logging.info(f"Webhook sent to {url}")
        return True


class MonolithicProcessor:
    """Main monolithic processor that combines all functionality."""
    
    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager("app.db")
        self.file_processor = FileProcessor(config)
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        self.report_generator = ReportGenerator(config)
        self.cache_manager = CacheManager()
        self.api_client = APIClient("https://api.example.com", "api_key")
        self.notification_service = NotificationService(config)
        self.logger = logging.getLogger(__name__)
    
    def initialize(self):
        """Initialize all components."""
        self.db_manager.connect()
        self.db_manager.create_tables()
        logging.info("MonolithicProcessor initialized")
    
    def cleanup(self):
        """Cleanup all components."""
        self.db_manager.disconnect()
        self.cache_manager.clear()
        logging.info("MonolithicProcessor cleaned up")
    
    def process_user_data(self, user_data: List[Dict]) -> Dict:
        """Process user data through the entire pipeline."""
        results = {
            'processed': 0,
            'errors': 0,
            'reports': []
        }
        
        for user_record in user_data:
            try:
                # Validate user data
                if not self.validator.validate_email(user_record.get('email', '')):
                    self.logger.warning(f"Invalid email: {user_record.get('email')}")
                    results['errors'] += 1
                    continue
                
                # Transform data
                normalized_name = self.transformer.normalize_text(user_record.get('name', ''))
                user_record['normalized_name'] = normalized_name
                
                # Store in database
                self.db_manager.execute_query(
                    "INSERT INTO users (name, email) VALUES (?, ?)",
                    (user_record.get('name'), user_record.get('email'))
                )
                
                # Cache processed data
                cache_key = f"user_{user_record.get('id')}"
                self.cache_manager.set(cache_key, user_record)
                
                results['processed'] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing user record: {e}")
                results['errors'] += 1
        
        # Generate reports
        summary_report = self.report_generator.generate_summary_report(user_data)
        detailed_report = self.report_generator.generate_detailed_report(user_data)
        
        results['reports'] = [summary_report, detailed_report]
        
        return results
    
    def process_order_data(self, order_data: List[Dict]) -> Dict:
        """Process order data through the pipeline."""
        results = {
            'processed': 0,
            'errors': 0,
            'notifications_sent': 0
        }
        
        for order_record in order_data:
            try:
                # Validate order data
                if not self.validator.validate_number(str(order_record.get('amount', 0))):
                    results['errors'] += 1
                    continue
                
                # Store in database
                self.db_manager.execute_query(
                    "INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, ?)",
                    (order_record.get('user_id'), order_record.get('product_id'), order_record.get('quantity'))
                )
                
                # Send notification
                user_email = self._get_user_email(order_record.get('user_id'))
                if user_email:
                    self.notification_service.send_email(
                        user_email,
                        "Order Confirmation",
                        f"Your order #{order_record.get('id')} has been processed."
                    )
                    results['notifications_sent'] += 1
                
                results['processed'] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing order record: {e}")
                results['errors'] += 1
        
        return results
    
    def _get_user_email(self, user_id: int) -> Optional[str]:
        """Get user email from database."""
        try:
            result = self.db_manager.execute_query(
                "SELECT email FROM users WHERE id = ?",
                (user_id,)
            )
            return result[0][0] if result else None
        except:
            return None
    
    def run_full_pipeline(self, user_data: List[Dict], order_data: List[Dict]) -> Dict:
        """Run the complete data processing pipeline."""
        self.initialize()
        
        try:
            # Process user data
            user_results = self.process_user_data(user_data)
            
            # Process order data
            order_results = self.process_order_data(order_data)
            
            # Generate final report
            final_report = {
                'timestamp': datetime.datetime.now().isoformat(),
                'user_processing': user_results,
                'order_processing': order_results,
                'total_processed': user_results['processed'] + order_results['processed'],
                'total_errors': user_results['errors'] + order_results['errors']
            }
            
            return final_report
            
        finally:
            self.cleanup()


def create_sample_data() -> Tuple[List[Dict], List[Dict]]:
    """Create sample data for testing."""
    user_data = []
    order_data = []
    
    # Create sample users
    for i in range(100):
        user_data.append({
            'id': i + 1,
            'name': f'User {i + 1}',
            'email': f'user{i + 1}@example.com',
            'phone': f'+123456789{i % 10}'
        })
    
    # Create sample orders
    for i in range(200):
        order_data.append({
            'id': i + 1,
            'user_id': (i % 100) + 1,
            'product_id': (i % 50) + 1,
            'quantity': random.randint(1, 5),
            'amount': round(random.uniform(10.0, 100.0), 2)
        })
    
    return user_data, order_data


def main():
    """Main function to demonstrate the monolithic processor."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create configuration
    config = Config(debug=True, max_workers=4)
    
    # Create processor
    processor = MonolithicProcessor(config)
    
    # Create sample data
    user_data, order_data = create_sample_data()
    
    # Run the pipeline
    results = processor.run_full_pipeline(user_data, order_data)
    
    # Print results
    print("Pipeline Results:")
    print(f"Total processed: {results['total_processed']}")
    print(f"Total errors: {results['total_errors']}")
    print(f"User processing: {results['user_processing']}")
    print(f"Order processing: {results['order_processing']}")


if __name__ == "__main__":
    main()