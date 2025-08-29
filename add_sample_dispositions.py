#!/usr/bin/env python3
"""
Add sample disposition data for testing.
"""

import pandas as pd
import random
import logging
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_sample_dispositions():
    """Add sample disposition data for testing."""
    try:
        if not config.CSV_FILE.exists():
            logger.error(f"CSV file not found: {config.CSV_FILE}")
            return False
        
        # Load existing data
        logger.info("Loading existing CSV data...")
        df = pd.read_csv(config.CSV_FILE)
        logger.info(f"Found {len(df)} records")
        
        # Sample dispositions for testing
        primary_dispositions = [
            'APPOINTMENT_SET', 'QUALIFIED_LEAD', 'NOT_QUALIFIED', 'NOT_INTERESTED',
            'CALLBACK_REQUESTED', 'WRONG_NUMBER', 'NO_ANSWER', 'HANG_UP',
            'VOICEMAIL', 'TECHNICAL_ISSUE', 'OTHER'
        ]
        
        secondary_dispositions = [
            'IMMEDIATE', 'FUTURE', 'PRICE_OBJECTION', 'TRUST_OBJECTION',
            'DECISION_MAKER', 'RESEARCH_NEEDED', 'COMPETITOR', 'SEASONAL',
            'BUDGET_CONSTRAINTS', 'PROPERTY_ISSUE', 'REFERRAL_NEEDED',
            'FOLLOW_UP_REQUIRED', 'OTHER'
        ]
        
        # Add sample dispositions to calls that don't have them
        count = 0
        for index, row in df.iterrows():
            if pd.isna(row['primary_disposition']) or row['primary_disposition'] == '':
                df.loc[index, 'primary_disposition'] = random.choice(primary_dispositions)
                df.loc[index, 'secondary_disposition'] = random.choice(secondary_dispositions)
                count += 1
        
        logger.info(f"Added sample dispositions to {count} records")
        
        # Save updated CSV
        df.to_csv(config.CSV_FILE, index=False)
        logger.info(f"Successfully updated CSV file: {config.CSV_FILE}")
        
        # Show disposition distribution
        primary_dist = df['primary_disposition'].value_counts()
        logger.info(f"Primary disposition distribution:\n{primary_dist}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding sample dispositions: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== ADDING SAMPLE DISPOSITIONS FOR TESTING ===")
    success = add_sample_dispositions()
    if success:
        logger.info("Successfully added sample dispositions")
    else:
        logger.error("Failed to add sample dispositions")