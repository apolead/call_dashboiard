"""
Sub-intent classifier for reprocessing existing call data.
Analyzes summaries and assigns appropriate sub-intents based on content.
"""

import pandas as pd
import re
import json
from typing import Dict, Optional
from openai import OpenAI
from config import config
import logging

logger = logging.getLogger(__name__)

class SubIntentClassifier:
    """Classifies calls into sub-intents based on summaries and intents."""
    
    def __init__(self):
        """Initialize the classifier."""
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Sub-intent mapping based on keywords and patterns
        self.sub_intent_patterns = {
            'ROOFING': {
                'ROOF_REPAIR': ['repair', 'leak', 'fix', 'damage', 'broken', 'leaking'],
                'ROOF_REPLACEMENT': ['replacement', 'replace', 'new roof', 'install'],
                'ROOF_INSPECTION': ['inspection', 'inspect', 'check', 'assessment'],
                'ROOF_PURCHASE': ['purchase', 'buy', 'material', 'gauge', 'buying'],
                'GUTTER_CLEANING': ['gutter clean', 'cleaning gutters', 'gutter maintenance'],
                'GUTTER_REPAIR': ['gutter repair', 'gutter fix', 'gutter damage']
            },
            'WINDOWS_DOORS': {
                'WINDOW_REPAIR': ['window repair', 'broken window', 'window fix'],
                'WINDOW_REPLACEMENT': ['window replacement', 'new window', 'replace window'],
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
                'ESTIMATE_REQUEST': ['estimate', 'quote', 'pricing', 'cost'],
                'CONSULTATION': ['consultation', 'consult', 'discuss', 'advice'],
                'PRICE_INQUIRY': ['price', 'how much', 'cost inquiry'],
                'SERVICE_COMPARISON': ['compare', 'comparison', 'options']
            },
            'OTHER': {
                'TEST_CALL': ['test call', 'testing', 'test'],
                'WRONG_NUMBER': ['wrong number', 'mistake', 'misdialed', 'not relevant'],
                'APPOINTMENT_SCHEDULING': ['appointment', 'schedule', 'booking'],
                'COMPLAINT': ['complaint', 'issue', 'problem', 'unhappy'],
                'GENERAL_INQUIRY': ['general', 'information', 'inquiry', 'question']
            }
        }
    
    def classify_sub_intent_by_keywords(self, intent: str, summary: str) -> str:
        """Classify sub-intent based on keywords in the summary."""
        if not intent or intent not in self.sub_intent_patterns:
            return 'GENERAL_INQUIRY'
        
        summary_lower = summary.lower()
        patterns = self.sub_intent_patterns[intent]
        
        # Score each sub-intent based on keyword matches
        scores = {}
        for sub_intent, keywords in patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in summary_lower:
                    score += 1
            scores[sub_intent] = score
        
        # Return the sub-intent with the highest score
        if scores and max(scores.values()) > 0:
            best_sub_intent = max(scores, key=scores.get)
            logger.info(f"Classified '{summary[:50]}...' as {intent} -> {best_sub_intent}")
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
            'OTHER': 'GENERAL_INQUIRY'
        }
        
        return defaults.get(intent, 'GENERAL_INQUIRY')
    
    def classify_sub_intent_with_ai(self, intent: str, summary: str, transcription: str = "") -> Optional[str]:
        """Use OpenAI to classify sub-intent more accurately."""
        try:
            # Create a focused prompt for sub-intent classification
            prompt = f"""
Based on this call summary and intent, determine the most specific sub-intent category.

Intent: {intent}
Summary: {summary}

Available sub-intents for {intent}:
"""
            
            if intent in self.sub_intent_patterns:
                for sub_intent in self.sub_intent_patterns[intent]:
                    prompt += f"- {sub_intent}\n"
            
            prompt += "\nRespond with ONLY the sub-intent name (e.g., ROOF_REPAIR)."
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at classifying home service call intents. Always respond with exactly one sub-intent category."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().upper()
            
            # Validate that the result is in our allowed sub-intents
            if intent in self.sub_intent_patterns and result in self.sub_intent_patterns[intent]:
                return result
            
        except Exception as e:
            logger.error(f"Error in AI sub-intent classification: {str(e)}")
        
        # Fallback to keyword classification
        return self.classify_sub_intent_by_keywords(intent, summary)
    
    def reprocess_data(self, csv_path: str, use_ai: bool = True) -> None:
        """Reprocess all data to assign proper sub-intents."""
        logger.info(f"Loading data from {csv_path}")
        df = pd.read_csv(csv_path)
        
        logger.info(f"Found {len(df)} records to process")
        
        updated_count = 0
        
        for index, row in df.iterrows():
            # Skip if already has a meaningful sub-intent
            if pd.notna(row['sub_intent']) and row['sub_intent'] != 'GENERAL_INQUIRY':
                continue
            
            intent = row.get('intent', 'OTHER')
            summary = row.get('summary', '')
            transcription = row.get('transcription', '')
            
            if pd.isna(summary) or summary == '':
                continue
            
            # Classify sub-intent
            if use_ai and len(summary) > 10:  # Use AI for meaningful summaries
                new_sub_intent = self.classify_sub_intent_with_ai(intent, summary, transcription)
            else:
                new_sub_intent = self.classify_sub_intent_by_keywords(intent, summary)
            
            # Update the dataframe
            df.at[index, 'sub_intent'] = new_sub_intent
            updated_count += 1
            
            if updated_count % 10 == 0:
                logger.info(f"Updated {updated_count} records...")
        
        # Save the updated data
        logger.info(f"Saving updated data with {updated_count} sub-intent classifications")
        df.to_csv(csv_path, index=False)
        
        # Print summary
        sub_intent_counts = df['sub_intent'].value_counts()
        logger.info("Sub-intent distribution:")
        for sub_intent, count in sub_intent_counts.items():
            logger.info(f"  {sub_intent}: {count}")

def main():
    """Main function to reprocess data."""
    logging.basicConfig(level=logging.INFO)
    classifier = SubIntentClassifier()
    classifier.reprocess_data(config.CSV_FILE, use_ai=True)

if __name__ == "__main__":
    main()