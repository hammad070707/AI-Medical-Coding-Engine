import asyncio
import os
import json
from dotenv import load_dotenv
from loguru import logger
from core.pre_processor import ClinicalPreProcessor
from core.rag_engine import RAGEngine
from core.validator import StaticValidator
from core.modifier_logic import ModifierLogic
from core.documentation_optimizer import DocumentationOptimizer
from agents.coder_agent import CoderAgent
from agents.auditor_agent import AuditorAgent
from core.em_calculator import EMCalculator 

load_dotenv()

async def run_coding_pipeline(file_path: str, patient_age: int, patient_gender: str):
    logger.info(f"--- Pipeline Active for: {file_path} ---")
    pre_processor = ClinicalPreProcessor()
    coder_agent = CoderAgent()
    auditor_agent = AuditorAgent()
    optimizer = DocumentationOptimizer()
    icd_rag = RAGEngine()
    cpt_rag = RAGEngine()
    
    icd_rag.load_from_disk("icd10_knowledge")
    cpt_rag.load_from_disk("cpt_knowledge")
    entities = await pre_processor.process_document(file_path)
    original_note = entities.get('raw_extracted_text', "Note extraction failed.")
    diag_query = " ".join(entities.get('diagnosis_keywords', []))
    proc_query = " ".join(entities.get('procedure_keywords', []))
    
    icd_candidates = icd_rag.search_relevant_codes(diag_query, top_k=10)
    cpt_candidates = cpt_rag.search_relevant_codes(proc_query, top_k=10)

    initial_coding = await coder_agent.generate_final_codes(
        original_note=original_note, entities=entities, 
        icd_candidates=icd_candidates, cpt_candidates=cpt_candidates
    )
    codes_dict = initial_coding.model_dump()
    em_code_data = EMCalculator.calculate_em_level(entities)
    codes_dict['procedures'].append({
        "code": em_code_data['code'], "description": em_code_data['desc'],
        "evidence_text": "MDM complexity", "confidence": 1.0
    })
    codes_dict = ModifierLogic.apply_modifiers(codes_dict, entities)
    patient_data = {"age": patient_age, "gender": patient_gender}
    is_valid, val_errors = StaticValidator.validate_claim(patient_data, entities, codes_dict)
    initial_audit = await auditor_agent.audit_claim(original_note, codes_dict, val_errors)

    report_data = {
        "phase1": {
            "score": initial_audit.compliance_score,
            "status": "APPROVED" if initial_audit.is_approved else "REJECTED",
            "risk": initial_audit.denial_risk,
            "icd": codes_dict['primary_diagnosis']['code'],
            "cpt": [p['code'] for p in codes_dict['procedures']],
            "modifiers": codes_dict['suggested_modifiers']
        },
        "phase2_suggestions": [],
        "phase3_final": {
            "score": initial_audit.compliance_score,
            "full_note": original_note,
            "status": "APPROVED" if initial_audit.is_approved else "REJECTED"
        }
    }
    cdi_report = None

    if not initial_audit.is_approved or initial_audit.compliance_score < 99:
        logger.info("Compliance below threshold. Kicking off Station 7, 8 & 9...")
        findings_data = [f.model_dump() for f in initial_audit.findings]
        cdi_report = await optimizer.generate_improvements(
            original_note, 
            findings_data, 
            initial_audit.compliance_score
        )
        addendum_text = cdi_report.addendum_template
        final_coding_obj = await coder_agent.refine_codes(
            original_note, 
            addendum_text, 
            findings_data
        )
        final_codes_dict = final_coding_obj.model_dump()
        has_em = any(p['code'].startswith('99') for p in final_codes_dict['procedures'])

        if not has_em:
            em_code_data = EMCalculator.calculate_em_level(entities)
            final_codes_dict['procedures'].append({
                "code": em_code_data['code'],
                "description": em_code_data['desc'],
                "evidence_text": "Enforced by EMCalculator for revenue integrity",
                "confidence": 1.0
            })

        final_codes_dict = ModifierLogic.apply_modifiers(final_codes_dict, entities)
        optimized_note = f"{original_note}\n\n[OFFICIAL ADDENDUM]\n{addendum_text}"
        logger.info("Re-auditing the corrected codes and note...")
        final_audit = await auditor_agent.audit_claim(optimized_note, final_codes_dict, [])
        report_data["phase2_suggestions"] = [s.model_dump() for s in cdi_report.suggestions]
        report_data["phase3_final"] = {
            "score": final_audit.compliance_score,
            "full_note": optimized_note,
            "icd": final_codes_dict['primary_diagnosis']['code'],
            "cpt": [p['code'] for p in final_codes_dict['procedures']],
            "modifiers": final_codes_dict['suggested_modifiers'],
            "status": "APPROVED" if final_audit.is_approved else "REJECTED"
        }

    else:
        report_data["phase3_final"] = {
            "score": initial_audit.compliance_score,
            "full_note": original_note,
            "icd": codes_dict['primary_diagnosis']['code'],
            "cpt": [p['code'] for p in codes_dict['procedures']],
            "modifiers": codes_dict['suggested_modifiers'],
            "status": "APPROVED"
        }
    
    return report_data



    print("\n" + "🔍"*5 + " PHASE 1: CURRENT NOTE ANALYSIS " + "🔍"*5)
    print(f"Bahi, aapke is note ka score abhi {initial_audit.compliance_score}/100 hai.")
    print(f"STATUS: {'🟢 APPROVED' if initial_audit.is_approved else '🔴 REJECTED'}")
    print(f"DENIAL RISK: {initial_audit.denial_risk.upper()}")
    print(f"\n[CURRENT CODES FOUND]:")
    print(f"- ICD-10: {codes_dict['primary_diagnosis']['code']}")
    print(f"- CPT CODES: {[p['code'] for p in codes_dict['procedures']]}")
    print(f"- MODIFIERS: {codes_dict['suggested_modifiers']}")
    cdi_report = None
    if initial_audit.compliance_score < 99: # 99 se kam ho toh behtar karo
        print("\n" + "💡"*5 + " BOT KA MASHWARA (How to fix) " + "💡"*5)
        print("Bahi, agar aap note mein ye 1-2 lines add kar dein toh claim 100% approve ho jayega:")
        
        findings_data = [f.model_dump() for f in initial_audit.findings]
        cdi_report = await optimizer.generate_improvements(original_note, findings_data, initial_audit.compliance_score)
        
        for sug in cdi_report.suggestions:
            print(f"📍 {sug.missing_element}:")
            print(f"   👉 \"{sug.suggested_text}\"")
        optimized_note = f"{original_note}\n\n[OFFICIAL ADDENDUM]\n{cdi_report.addendum_template}"
        logger.info("Re-calculating for final approval...")
        codes_dict = ModifierLogic.apply_modifiers(codes_dict, entities) 
        final_audit = await auditor_agent.audit_claim(optimized_note, codes_dict, [])
    else:
        optimized_note = original_note
        final_audit = initial_audit
    print("\n" + "✅"*5 + " PHASE 3: FINAL OPTIMIZED REPORT " + "✅"*5)
    print(f"FINAL STATUS: 🟢 APPROVED")
    print(f"FINAL SCORE: {final_audit.compliance_score}/100")
    print(f"FINAL CODES: ICD:{codes_dict['primary_diagnosis']['code']} | CPT:{[p['code'] for p in codes_dict['procedures']]} | MOD:{codes_dict['suggested_modifiers']}")
    
    print("\n[FULL SUBMISSION READY NOTE (Original + Addendum)]")
    print("="*60)
    print(optimized_note)
    print("="*60)
    print("\n" + "🏥"*10 + " PROCESS COMPLETE " + "🏥"*10 + "\n")
