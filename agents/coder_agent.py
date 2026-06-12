import os
import json
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from loguru import logger

class CodeEvidence(BaseModel):
    code: str=Field(description="The ICD-10 or CPT code")
    description: str = Field(description="Official description of the code")
    evidence_text: str = Field(description="Exact quote from the doctor's note that justifies this code")
    confidence:float = Field(description="Score between 0 and 1")

class CodingResponse(BaseModel):
    primary_diagnosis: CodeEvidence
    secondary_diagnoses: List[CodeEvidence]
    procedures: List[CodeEvidence]
    suggested_modifiers: List[str] = Field(description="Potential modifiers like -25, -59, -RT based on note")
    complexity_level: str
    place_of_service: str = Field(description="e.g., Office (11), ER (23), Inpatient (21)")
    medical_necessity_score: float = Field(description="0 to 1 score: Do procedures match the diagnosis?")
    unbundling_alert: bool = Field(description="True if multiple procedures might be part of a single code (NCCI edits)")
    coding_rationale: str = Field(description="Detailed explanation of why these codes were chosen")

class CoderAgent:
    def __init__(self):
        logger.info("Initializing Senior Coder Agent...")
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    async def generate_final_codes(
        self,
        original_note: str,
        entities: Dict,
        icd_candidates: List[Dict],
        cpt_candidates: List[Dict]
    ) -> CodingResponse:
        
        system_prompt = """
        You are a Senior Certified Professional Coder (CPC) with 30 years of experience.
        Your task is to assign the most accurate ICD-10-CM and CPT-4 codes based on the clinical note.
        
        RULES:
        1. Accuracy is 100% Mandatory. Assign codes only if supported by evidence.
        2. PRIMARY DIAGNOSIS RULE: The 'Chief Complaint' (the reason for the visit) MUST be the Primary ICD-10 code. Chronic conditions (Diabetes, HTN) are SECONDARY unless they are the main reason for today's visit.
        3. CLINICAL SPECIFICITY & GRANULARITY: 
            - Always prioritize the most granular and specific code available in the RAG candidates.
            - If a specific test, antigen, or anatomical site is named (e.g., "Streptococcus Group A" or "Right distal radius"), do NOT assign a generic or "unspecified" category code if a more precise matching code exists in the candidates.
            - Example: Prefer 87880 (Specific for Strep A) over 87802 (Generic infectious agent) if the note specifies "Rapid Strep".
        4. Identify Laterality (Left/Right) and include it in your rationale.
        5. For every code, provide the 'evidence_text' (the exact snippet from the note).
        6. MODIFIER -25 LOGIC: Only assign -25 if the E&M visit is for a SIGNIFICANT and SEPARATELY identifiable issue (like uncontrolled DM/HTN) apart from the procedure (like stitches)
        7. MANDATORY E&M CODING: Every encounter must have at least one Evaluation & Management (E&M) code (e.g., 99202-99215 for office visits)
        If no specific surgery/test is performed, assign the correct E&M level based on the complexity (Low, Moderate, High).
        8. EVIDENCE-BASED ONLY: If the note doesn't say it, don't code it. No guessing
        9. MEASUREMENT ACCURACY: 
           - For lacerations (CPT 12001-12007), you MUST match the 'cm' mentioned in the note exactly to the CPT description.
           - Rule: 12001 (up to 2.5 cm), 12002 (2.6 cm to 7.5 cm), 12004 (7.6 cm to 12.5 cm).
           - Do NOT round up. A 5 cm wound is 12002. Using 12004 is FRAUD.
        10. STRICT CPT ADD-ON RULE: 
        Never assign an add-on code (like 17003) without its primary code (like 17000). 
        STRICT MEASUREMENT RULE: 
        Do not round up centimeters. Always use the exact sum of lesion diameter + margins to pick the CPT range. Cross-verify the description twice.
        11. FORMATTING RULE: 'laterality' field must ALWAYS be a single string (e.g., 'Left', 'Right', 'Bilateral', or 'Multiple'). Never return a dictionary or nested object for this field.
        """
        
        user_prompt = f"""
        CLINICAL NOTE:
        {original_note}

        EXTRACTED ENTITIES (Pre-Processor):
        {json.dumps(entities, indent=2)}
        

        CANDIDATE ICD-10 CODES (from Vector DB):
        {json.dumps(icd_candidates, indent=2)}

        CANDIDATE CPT CODES (from Vector DB):
        {json.dumps(cpt_candidates, indent=2)}

        Analyze the note, compare it with candidate codes, and return the final coding in JSON.
        """

        try:
            logger.info("Generating final codes...")
            response= await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role":"system","content":system_prompt},
                    {"role":"user","content":user_prompt}
                ],
                response_format=CodingResponse,
                temperature=0.1
            )
            final_output=response.choices[0].message.parsed
            logger.info("Final codes generated successfully.")
            return final_output
        
        except Exception as e:
            logger.error(f"Error generating final codes: {e}")
            raise

    async def refine_codes(self, original_note: str, addendum: str, audit_findings: list) -> CodingResponse:
        """
        Judge (Auditor) ke aiterazat ke mutabiq codes ko final update karna.
        """
        logger.info("Refining codes based on Auditor feedback...")
        
        refine_prompt = f"""
        You previously assigned codes that were CRITIQUED by an Auditor.
        
        ORIGINAL NOTE: {original_note}
        OFFICIAL ADDENDUM: {addendum}
        AUDITOR FINDINGS: {json.dumps(audit_findings)}
        
        YOUR TASK:
        1. Correct the CPT/ICD codes based on the Auditor's suggestions and the Addendum.
        2. Ensure the final JSON reflects the 100% accurate codes for submission.
        3. If the Auditor said 'Remove Modifier -25', then remove it.
        4. If the Auditor said 'Use CPT 73610 instead of 73615', make that change.
        """

        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Senior Coder performing final data reconciliation."},
                {"role": "user", "content": refine_prompt}
            ],
            response_format=CodingResponse,
            temperature=0.0
        )
        return response.choices[0].message.parsed
