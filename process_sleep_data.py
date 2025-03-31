import pandas as pd
import json
from datetime import datetime
import logging
import chardet
import zipfile
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_file_content(file_path):
    """Read file content and handle different formats"""
    try:
        # Try reading as regular file first
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # Try to detect if it's a zip file
        if content.startswith(b'PK\x03\x04'):
            logger.info("File appears to be a ZIP archive")
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                # Look for CSV file in the archive
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                if not csv_files:
                    raise Exception("No CSV file found in ZIP archive")
                logger.info(f"Found CSV file: {csv_files[0]}")
                return zf.read(csv_files[0])
        
        return content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise

def parse_date(date_str):
    """Parse date string in format 'DD. MM. YYYY HH:MM'"""
    try:
        if pd.isna(date_str):
            return None
        return datetime.strptime(date_str.strip(), '%d. %m. %Y %H:%M')
    except (ValueError, AttributeError):
        return None

def process_sleep_data(input_file, output_file):
    """Process sleep data from CSV and save to JSON"""
    logger.info(f"Reading data from {input_file}")
    
    try:
        # Read file content
        content = read_file_content(input_file)
        
        # Detect encoding
        result = chardet.detect(content)
        encoding = result['encoding']
        logger.info(f"Detected encoding: {encoding}")
        
        # Try different encodings if the detected one doesn't work
        encodings_to_try = [encoding] if encoding else ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        
        df = None
        for enc in encodings_to_try:
            try:
                logger.info(f"Trying {enc} encoding...")
                # Read CSV with a large number of columns to handle varying data
                df = pd.read_csv(io.BytesIO(content), encoding=enc, on_bad_lines='skip')
                logger.info(f"Successfully read with {enc} encoding")
                break
            except Exception as e:
                logger.error(f"Error reading CSV with {enc} encoding: {str(e)}")
                continue
        
        if df is None:
            raise Exception("Could not read CSV file with any supported encoding")
        
        # Print DataFrame info
        logger.info("DataFrame columns:")
        logger.info(df.columns.tolist())
        logger.info("\nFirst few rows:")
        logger.info(df.head())
        
        # Initialize list to store processed sleep records
        sleep_records = []
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Skip rows with missing essential data
                if pd.isna(row['Id']) or pd.isna(row['From']) or pd.isna(row['To']):
                    continue
                    
                # Parse dates
                from_time = parse_date(row['From'])
                to_time = parse_date(row['To'])
                sched_time = parse_date(row['Sched']) if not pd.isna(row['Sched']) else None
                
                if not from_time or not to_time:
                    continue
                
                # Create sleep record
                sleep_record = {
                    'id': str(row['Id']),
                    'timezone': row['Tz'],
                    'fromTime': int(from_time.timestamp() * 1000),
                    'toTime': int(to_time.timestamp() * 1000),
                    'scheduledTime': int(sched_time.timestamp() * 1000) if sched_time else None,
                    'hours': float(row['Hours']) if not pd.isna(row['Hours']) else None,
                    'rating': float(row['Rating']) if not pd.isna(row['Rating']) else None,
                    'comment': row['Comment'] if not pd.isna(row['Comment']) else None,
                    'framerate': int(row['Framerate']) if not pd.isna(row['Framerate']) else None,
                    'snore': float(row['Snore']) if not pd.isna(row['Snore']) else None,
                    'noise': float(row['Noise']) if not pd.isna(row['Noise']) else None,
                    'cycles': int(row['Cycles']) if not pd.isna(row['Cycles']) else None,
                    'deepSleep': float(row['DeepSleep']) if not pd.isna(row['DeepSleep']) else None,
                    'lenAdjust': int(row['LenAdjust']) if not pd.isna(row['LenAdjust']) else None,
                    'geo': row['Geo'] if not pd.isna(row['Geo']) else None
                }
                
                # Add events if they exist
                events = []
                for col in df.columns:
                    if col.startswith('Event') and not pd.isna(row[col]):
                        events.append(row[col])
                if events:
                    sleep_record['events'] = events
                
                sleep_records.append(sleep_record)
                
            except Exception as e:
                logger.error(f"Error processing row {row['Id']}: {str(e)}")
                continue
        
        # Save to JSON file
        logger.info(f"Saving {len(sleep_records)} records to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'sleeps': sleep_records}, f, indent=2)
        
        logger.info("Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise

if __name__ == "__main__":
    input_file = "sleep-export.csv"
    output_file = "sleep_data_2016_to_2025.json"
    process_sleep_data(input_file, output_file) 