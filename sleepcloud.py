import requests
import json
from datetime import datetime
import time
import os
from typing import Dict, List, Optional
import logging
import shutil
from pathlib import Path
import sys
from dataclasses import dataclass
from json.decoder import JSONDecodeError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sleep_cloud.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProgressState:
    """Class to track and persist fetch progress"""
    current_timestamp: int
    total_records: int
    last_save_time: float

    @classmethod
    def load(cls, filename: str) -> Optional['ProgressState']:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                return cls(
                    current_timestamp=data['current_timestamp'],
                    total_records=data['total_records'],
                    last_save_time=data['last_save_time']
                )
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def save(self, filename: str) -> None:
        with open(filename, 'w') as f:
            json.dump({
                'current_timestamp': self.current_timestamp,
                'total_records': self.total_records,
                'last_save_time': self.last_save_time
            }, f)

class SleepCloudClient:
    def __init__(self, user_token: str):
        if not isinstance(user_token, str) or not user_token.strip():
            raise ValueError("Invalid user token")
        
        self.base_url = "https://sleep-cloud.appspot.com/fetchRecords"
        self.user_token = user_token
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SleepCloudDataFetcher/1.0'
        })
        
    def validate_sleep_record(self, record: Dict) -> bool:
        """Validate sleep record data structure and values."""
        required_fields = {'fromTime', 'toTime', 'quality'}
        
        if not all(field in record for field in required_fields):
            return False
            
        try:
            # Validate timestamp values
            if not (isinstance(record['fromTime'], (int, float)) and 
                   isinstance(record['toTime'], (int, float))):
                return False
                
            # Ensure fromTime is before toTime
            if record['fromTime'] >= record['toTime']:
                return False
                
            # Validate quality score
            if not (isinstance(record['quality'], (int, float)) and 
                   0 <= record['quality'] <= 100):
                return False
                
            return True
        except Exception:
            return False

    def fetch_sleep_records(self, timestamp: int) -> List[Dict]:
        """Fetch sleep records for a given timestamp."""
        if not isinstance(timestamp, int) or timestamp <= 0:
            raise ValueError("Invalid timestamp")
            
        params = {"user_token": self.user_token, "timestamp": str(timestamp)}
        try:
            response = self.session.get(
                self.base_url, 
                params=params,
                timeout=30  # 30 second timeout
            )
            response.raise_for_status()
            
            try:
                data = response.json()
            except JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {e}")
                return []
                
            sleep_records = data.get("sleeps", [])
            
            # Validate and filter records
            valid_records = [
                record for record in sleep_records 
                if self.validate_sleep_record(record)
            ]
            
            if len(valid_records) < len(sleep_records):
                logger.warning(
                    f"Filtered out {len(sleep_records) - len(valid_records)} invalid records"
                )
                
            return valid_records
            
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching records: {e}")
            return []

def backup_file(file_path: str) -> None:
    """Create a backup of the specified file."""
    if not os.path.exists(file_path):
        return
        
    backup_path = f"{file_path}.backup"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")

def save_data_chunk(data: List[Dict], filename: str, mode: str = 'w') -> None:
    """Save data chunk to file with proper error handling."""
    temp_file = f"{filename}.tmp"
    try:
        with open(temp_file, mode) as f:
            if mode == 'w':
                json.dump({"sleeps": data}, f, indent=2)
            else:  # append mode
                f.write(',\n'.join(json.dumps(record) for record in data))
                
        # Atomic replace
        os.replace(temp_file, filename)
    except Exception as e:
        logger.error(f"Error saving data chunk: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise

def main():
    # Get user token from environment variable
    user_token = os.getenv("SLEEP_CLOUD_TOKEN")
    if not user_token:
        logger.error("Please set SLEEP_CLOUD_TOKEN environment variable")
        return

    # Initialize client
    try:
        client = SleepCloudClient(user_token)
    except ValueError as e:
        logger.error(f"Client initialization failed: {e}")
        return
    
    # Timestamps (in milliseconds)
    start_time = 1451606400000  # Jan 1, 2016, 00:00:00 GMT+03:00
    end_time = 1743465599000    # Mar 31, 2025, 23:59:59 GMT+03:00
    
    output_file = "sleep_data_2016_to_2025.json"
    progress_file = ".sleep_fetch_progress"
    chunk_size = 100  # Number of records to process before saving
    
    # Try to resume from previous state
    progress = ProgressState.load(progress_file)
    if progress:
        logger.info(f"Resuming from previous session (timestamp: {progress.current_timestamp})")
        current_timestamp = progress.current_timestamp
        all_sleeps_count = progress.total_records
    else:
        current_timestamp = end_time
        all_sleeps_count = 0
    
    # Create backup of existing output file
    backup_file(output_file)
    
    # Initialize output file if starting fresh
    if not progress:
        save_data_chunk([], output_file)
    
    retry_count = 0
    max_retries = 3
    current_chunk = []
    
    try:
        while current_timestamp > start_time:
            try:
                # Fetch records with rate limiting
                sleep_records = client.fetch_sleep_records(current_timestamp)
                
                if not sleep_records:
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.warning(f"No records found. Retry {retry_count}/{max_retries}")
                        time.sleep(5)  # Wait 5 seconds before retry
                        continue
                    else:
                        logger.info("No more records found after retries.")
                        break
                
                # Reset retry count on successful fetch
                retry_count = 0
                
                # Add new records to the current chunk
                current_chunk.extend(sleep_records)
                all_sleeps_count += len(sleep_records)
                
                # Save progress periodically
                if len(current_chunk) >= chunk_size:
                    save_data_chunk(current_chunk, output_file, 'a')
                    current_chunk = []
                    
                    # Update progress state
                    progress = ProgressState(
                        current_timestamp=current_timestamp,
                        total_records=all_sleeps_count,
                        last_save_time=time.time()
                    )
                    progress.save(progress_file)
                
                logger.info(
                    f"Fetched {len(sleep_records)} records. "
                    f"Total so far: {all_sleeps_count}"
                )
                
                # Update timestamp to the earliest fromTime in this batch
                current_timestamp = min(record["fromTime"] for record in sleep_records)
                logger.info(
                    f"Next timestamp: {datetime.fromtimestamp(current_timestamp / 1000)} UTC+3"
                )
                
                # Rate limiting
                time.sleep(1)  # Wait 1 second between requests
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(5)
                    continue
                break
        
        # Save any remaining records
        if current_chunk:
            save_data_chunk(current_chunk, output_file, 'a')
        
        logger.info(
            f"Successfully completed. Total records saved: {all_sleeps_count}"
        )
        
        # Clean up progress file
        if os.path.exists(progress_file):
            os.remove(progress_file)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Progress has been saved.")
        if current_chunk:
            save_data_chunk(current_chunk, output_file, 'a')
        sys.exit(1)

if __name__ == "__main__":
    main()