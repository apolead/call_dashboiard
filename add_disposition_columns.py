#!/usr/bin/env python3
"""
Add disposition columns to existing CSV data.
"""

import pandas as pd
import logging
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_disposition_columns():
    """Add primary_disposition and secondary_disposition columns to existing CSV."""
    try:
        if not config.CSV_FILE.exists():
            logger.error(f"CSV file not found: {config.CSV_FILE}")
            return False
        
        # Load existing data
        logger.info("Loading existing CSV data...")
        df = pd.read_csv(config.CSV_FILE)
        logger.info(f"Found {len(df)} records")
        
        # Check if columns already exist
        if 'primary_disposition' in df.columns and 'secondary_disposition' in df.columns:
            logger.info("Disposition columns already exist!")
            return True
        
        # Add new columns with empty values
        if 'primary_disposition' not in df.columns:
            df['primary_disposition'] = ''
            logger.info("Added primary_disposition column")
            
        if 'secondary_disposition' not in df.columns:
            df['secondary_disposition'] = ''
            logger.info("Added secondary_disposition column")
        
        # Save updated CSV
        df.to_csv(config.CSV_FILE, index=False)
        logger.info(f"Successfully updated CSV file: {config.CSV_FILE}")
        
        # Display updated column names
        logger.info(f"Updated columns: {list(df.columns)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding disposition columns: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== ADDING DISPOSITION COLUMNS ===")
    success = add_disposition_columns()
    if success:
        logger.info("✅ Successfully added disposition columns")
    else:
        logger.error("❌ Failed to add disposition columns")