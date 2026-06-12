import os
import json
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from loguru import logger

class AuditFinding(BaseModel):
    error_type: str = Field(description="e.g., Medical Necessity, Upcoding, Improper Modifier, Documentation Gap")
    severity: str = Field(description="Low, Medium, High, or Critical")
    description: str = Field(description="Explanation of the clinical or logical error")
    correction_suggestion: str = Field(description="Specific steps to fix the claim")

class AuditResponse(BaseModel):
    is_approved: bool = Field(description="True only if the claim is 100% safe to submit")
    compliance_score: float = Field(description="Accuracy score from 0 to 100")
    findings: List[AuditFinding] = Field(default_factory=list)
    denial_risk: str = Field(description="Predicted risk: Low, Moderate, High, or Certain Denial")
    final_auditor_summary: str = Field(description="The senior auditor's final advice")

class AuditorAgent:

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = "gpt-4o"

    async def audit_claim(self, original_note: str, coder_output: str, validation_errors: List[str]) -> AuditResponse:
        
        """
        Yeh function Coder ke kaam ka Post-Mortem karta hai.
        """

        system_prompt = """
        You are a Senior Medical Auditor with 35 years of experience in Revenue Cycle Management (RCM).
        Your mission is to find reasons why an insurance company (like Aetna or BlueCross) would REJECT this claim.

        AUDIT FOCUS:
        1. MEDICAL NECESSITY: Does the clinical note actually justify the procedures performed?
        2. DOCUMENTATION GAP: Is there enough detail in the note to support the assigned CPT level?
        3. UPCODING: Did the coder assign a high-level E&M (e.g., 99215) for a simple case?
        4. UNBUNDLING: Check if procedures should be reported together under one code.
        5. VALIDATOR REVIEW: I will provide hard-coded errors found by the Static Validator. Include them in your final verdict.
        6. ADDENDUM RULE (IMPORTANT): 
           If the clinical note contains an 'ADDENDUM' section, you MUST evaluate the documentation as a COMBINED whole. 
           If the addendum provides the missing details (like justifying Modifier -25 or explaining Medical Decision Making), 
           you should increase the compliance score to 95+ and set 'is_approved' to True. 
           Be fair—if the legal documentation requirements are now met, approve the claim.
        7. 7. MULTI-PROCEDURE AUDIT: If there are multiple surgical procedures (like Excision + Cryosurgery), check if Modifier -59 is correctly applied. If it's missing, the compliance score must drop below 85.
        """

        user_prompt = f"""
        [CLINICAL NOTE]
        {original_note}

        [CODER AGENT PROPOSED CODES]
        {json.dumps(coder_output, indent=2)} 

        [STATIC VALIDATOR HARD ERRORS]
        {json.dumps(validation_errors, indent=2)}

        Analyze the entire encounter. Be strict. If the note is weak, flag it for human review.
        """
        
        try:
            logger.info("audit_claim() called")
            response=await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=AuditResponse,
                temperature=0.0

            )
            
            audit_result = response.choices[0].message.parsed
            logger.info(f"audit_claim() completed successfully: {audit_result}")
            
            if not audit_result.is_approved:
                logger.warning(f"Auditor REJECTED claim. Denial Risk: {audit_result.denial_risk}")
            else:
                logger.success(f"Auditor APPROVED claim. Compliance Score: {audit_result.compliance_score}")
            
            return audit_result
        
        except Exception as e:
            logger.error(f"audit_claim() failed: {e}")
            raise

