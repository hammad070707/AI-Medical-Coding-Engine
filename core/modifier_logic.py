from typing import List, Dict
from loguru import logger

class ModifierLogic:    
    @staticmethod
    def apply_modifiers(coder_output: Dict, entities: Dict) -> Dict:
        logger.info("Applying Modifiers...")        
        procedures = coder_output.get("procedures", [])
        final_modifiers = set(coder_output.get('suggested_modifiers', []))        
        em_codes = [p for p in procedures if p['code'].startswith('99')]
        non_em_procedures = [p for p in procedures if not p['code'].startswith('99')]

        if len(non_em_procedures) > 0 and len(em_codes) > 0:
            if "-25" not in final_modifiers:
                final_modifiers.add("-25") 
                logger.success(f"Dynamic Rule: Modifier -25 added because {len(non_em_procedures)} procedures were found with E&M.")
        lat_raw = entities.get('laterality', 'None')
        
        if isinstance(lat_raw, dict):
            laterality = " ".join(str(v) for v in lat_raw.values()).upper()

        elif isinstance(lat_raw, list):
            laterality = " ".join(str(v) for v in lat_raw).upper()

        else:
            laterality = str(lat_raw).upper()
        
        if "RIGHT" in laterality and "LEFT" in laterality:
            final_modifiers.add("-RT")
            final_modifiers.add("-LT")
            logger.success("Dynamic Rule: Added both -RT and -LT for multiple body parts.")
            
        elif "RIGHT" in laterality: 
            if "-RT" not in final_modifiers:
                final_modifiers.add("-RT")
                logger.success("Strict Rule: Force added -RT based on note.")
                
        elif "LEFT" in laterality:
            if "-LT" not in final_modifiers:
                final_modifiers.add("-LT")
                logger.success("Strict Rule: Force added -LT based on note.")
                
        elif "BILATERAL" in laterality or "50" in laterality:
            final_modifiers.add("-50")
            logger.success("Rule Applied: Modifier -50 for bilateral service.")              
            
        if len(non_em_procedures) >= 2:
            if "-59" not in final_modifiers:
                final_modifiers.add("-59")
                logger.warning("Rule Applied: Distinct Procedural Service (-59) added for multiple non-E&M procedures.")
        else:
            logger.info("Rule Skipped: -59 not needed (Single Procedure detected).")

        coder_output['suggested_modifiers'] = list(final_modifiers) 
        return coder_output

    @staticmethod
    def clean_modifiers(modifiers: List[str]) -> List[str]:
        return [m.replace("-", "").strip() for m in modifiers]
    


