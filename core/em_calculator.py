from typing import Dict
from loguru import logger

class EMCalculator:
    """
    STATION: E&M Leveling Engine
    Maqsad: Medical Decision Making (MDM) ke hisab se Office Visit code (99211-99215) nikalna.
    """

    @staticmethod
    def calculate_em_level(entities: Dict) -> Dict:
        """
        MDM Complexity (Low, Moderate, High) aur Location ke mutabiq code assign karta hai.
        """

        complexity = entities.get('complexity', 'Low').upper()
        location = entities.get('location', 'Clinic').upper()
        em_codes = {
            "CLINIC": {
                "LOW": {"code": "99213", "desc": "Office visit, established patient, low complexity"},
                "MODERATE": {"code": "99214", "desc": "Office visit, established patient, moderate complexity"},
                "HIGH": {"code": "99215", "desc": "Office visit, established patient, high complexity"}
            },
            "ER": {
                "LOW": {"code": "99282", "desc": "ER visit, low complexity"},
                "MODERATE": {"code": "99283", "desc": "ER visit, moderate complexity"},
                "HIGH": {"code": "99284", "desc": "ER visit, high complexity"}
            }
        }

        loc_key = "CLINIC" if "CLINIC" in location or "OFFICE" in location else "ER"
        
        selected_em = em_codes.get(loc_key, em_codes["CLINIC"]).get(complexity, em_codes["CLINIC"]["LOW"])
        
        logger.info(f"E&M Calculator: Assigned {selected_em['code']} based on {complexity} complexity at {loc_key}.")

        return selected_em