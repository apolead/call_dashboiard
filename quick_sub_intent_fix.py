"""
Quick sub-intent classifier using keyword matching.
Fast processing for existing call data.
"""

import pandas as pd
import re
import logging
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def classify_sub_intent(intent: str, summary: str) -> str:
    """Classify sub-intent based on keywords in the summary."""
    
    # Sub-intent patterns based on keywords
    patterns = {
        'ROOFING': {
            'ROOF_PURCHASE': ['purchase', 'buy', 'material', 'gauge', 'buying', 'advertised', 'facebook'],
            'ROOF_REPAIR': ['repair', 'leak', 'fix', 'damage', 'broken', 'leaking'],
            'ROOF_REPLACEMENT': ['replacement', 'replace', 'new roof', 'install'],
            'ROOF_INSPECTION': ['inspection', 'inspect', 'check', 'assessment'],
            'GUTTER_CLEANING': ['gutter clean', 'cleaning gutters', 'gutter maintenance'],
            'GUTTER_REPAIR': ['gutter repair', 'gutter fix', 'gutter damage']
        },
        'WINDOWS_DOORS': {
            'WINDOW_REPAIR': ['window repair', 'broken window', 'window fix', 'upstairs window'],
            'WINDOW_REPLACEMENT': ['window replacement', 'new window', 'replace window', 'glass block windows'],
            'DOOR_REPAIR': ['door repair', 'broken door', 'door fix'],
            'DOOR_INSTALLATION': ['door install', 'new door', 'door replacement'],
            'SCREEN_REPAIR': ['screen repair', 'screen replacement', 'screen fix']
        },
        'PLUMBING': {
            'LEAK_REPAIR': ['leak', 'leaking', 'water damage', 'pipe leak'],
            'PIPE_REPAIR': ['pipe repair', 'broken pipe', 'pipe fix'],
            'DRAIN_CLEANING': ['drain clean', 'clogged drain', 'drain maintenance'],
            'TOILET_REPAIR': ['toilet repair', 'toilet fix', 'toilet problem'],
            'FAUCET_REPAIR': ['faucet repair', 'faucet fix', 'tap repair'],
            'WATER_HEATER': ['water heater', 'hot water', 'heater repair']
        },
        'ELECTRICAL': {
            'WIRING_REPAIR': ['wiring', 'electrical problem', 'wire repair'],
            'OUTLET_INSTALLATION': ['outlet', 'electrical outlet', 'socket install'],
            'LIGHTING_REPAIR': ['lighting', 'light repair', 'light fix'],
            'ELECTRICAL_INSPECTION': ['electrical inspect', 'electrical check'],
            'PANEL_UPGRADE': ['electrical panel', 'panel upgrade', 'breaker box']
        },
        'HVAC': {
            'AC_REPAIR': ['ac repair', 'air conditioning', 'ac fix', 'cooling'],
            'HEATING_REPAIR': ['heating repair', 'heater', 'heat pump', 'furnace'],
            'DUCT_CLEANING': ['duct clean', 'air duct', 'ductwork'],
            'SYSTEM_INSTALLATION': ['hvac install', 'system install', 'new hvac'],
            'MAINTENANCE_SERVICE': ['hvac maintenance', 'service call', 'tune up']
        },
        'KITCHEN_BATH': {
            'BATHROOM_REMODEL': ['bathroom remodel', 'bath renovation', 'bathroom renovation'],
            'KITCHEN_REMODEL': ['kitchen remodel', 'kitchen renovation', 'kitchen upgrade'],
            'SHOWER_INSTALLATION': ['shower install', 'new shower', 'shower replacement'],
            'COUNTERTOP_REPAIR': ['countertop', 'counter repair', 'counter replacement'],
            'TILE_WORK': ['tile work', 'tile repair', 'tile installation']
        },
        'QUOTE_REQUEST': {
            'ESTIMATE_REQUEST': ['estimate', 'quote', 'pricing', 'cost', 'looking for a quote'],
            'CONSULTATION': ['consultation', 'consult', 'discuss', 'advice', 'listing', 'website'],
            'PRICE_INQUIRY': ['price', 'how much', 'cost inquiry'],
            'SERVICE_COMPARISON': ['compare', 'comparison', 'options']
        },
        'EMERGENCY_REPAIR': {
            'EMERGENCY_REPAIR': ['emergency', 'urgent', 'asap', 'immediately']
        },
        'COMPLAINT': {
            'COMPLAINT': ['complaint', 'issue', 'problem', 'unhappy', 'dissatisfied']
        },
        'GENERAL_CONTRACTOR': {
            'GENERAL_INQUIRY': ['general', 'contractor', 'multiple', 'various']
        },
        'OTHER': {
            'TEST_CALL': ['test call', 'testing', 'test', 'prepare for incoming leads', 'be ready'],
            'WRONG_NUMBER': ['wrong number', 'mistake', 'misdialed', 'not relevant', 'at&t', 'internet service', 'business internet'],
            'APPOINTMENT_SCHEDULING': ['appointment', 'schedule', 'booking'],
            'COMPLAINT': ['complaint', 'issue', 'problem', 'unhappy'],
            'GENERAL_INQUIRY': ['greeting', 'audio clarity', 'confirming', 'brief', 'no specific inquiry', 'information']
        }
    }
    
    if not intent or intent not in patterns:
        return 'GENERAL_INQUIRY'
    
    summary_lower = summary.lower()
    intent_patterns = patterns[intent]
    
    # Score each sub-intent based on keyword matches
    scores = {}
    for sub_intent, keywords in intent_patterns.items():
        score = 0
        for keyword in keywords:
            if keyword in summary_lower:
                score += len(keyword)  # Longer keywords get higher scores
        scores[sub_intent] = score
    
    # Return the sub-intent with the highest score
    if scores and max(scores.values()) > 0:
        best_sub_intent = max(scores, key=scores.get)
        return best_sub_intent
    
    # Default based on intent
    defaults = {
        'ROOFING': 'ROOF_REPAIR',
        'WINDOWS_DOORS': 'WINDOW_REPAIR', 
        'PLUMBING': 'LEAK_REPAIR',
        'ELECTRICAL': 'WIRING_REPAIR',
        'HVAC': 'AC_REPAIR',
        'KITCHEN_BATH': 'BATHROOM_REMODEL',
        'QUOTE_REQUEST': 'ESTIMATE_REQUEST',
        'EMERGENCY_REPAIR': 'EMERGENCY_REPAIR',
        'COMPLAINT': 'COMPLAINT',
        'GENERAL_CONTRACTOR': 'GENERAL_INQUIRY',
        'OTHER': 'GENERAL_INQUIRY'
    }
    
    return defaults.get(intent, 'GENERAL_INQUIRY')

def main():
    """Main function to reprocess data."""
    logger.info(f"Loading data from {config.CSV_FILE}")
    df = pd.read_csv(config.CSV_FILE)
    
    logger.info(f"Found {len(df)} records to process")
    
    updated_count = 0
    
    for index, row in df.iterrows():
        intent = row.get('intent', 'OTHER')
        summary = row.get('summary', '')
        
        if pd.isna(summary) or summary == '':
            df.at[index, 'sub_intent'] = 'GENERAL_INQUIRY'
            continue
        
        # Classify sub-intent using keywords
        new_sub_intent = classify_sub_intent(intent, summary)
        
        # Update the dataframe
        df.at[index, 'sub_intent'] = new_sub_intent
        updated_count += 1
        
        if updated_count % 20 == 0:
            logger.info(f"Updated {updated_count} records...")
    
    # Save the updated data
    logger.info(f"Saving updated data with {updated_count} sub-intent classifications")
    df.to_csv(config.CSV_FILE, index=False)
    
    # Print summary
    sub_intent_counts = df['sub_intent'].value_counts()
    logger.info("Sub-intent distribution:")
    for sub_intent, count in sub_intent_counts.head(15).items():
        logger.info(f"  {sub_intent}: {count}")
    
    logger.info("Sub-intent classification complete!")

if __name__ == "__main__":
    main()