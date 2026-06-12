import os
from typing import List , Dict
from pydantic import BaseModel,Field
from openai import AsyncOpenAI
from loguru import logger

class ImprovementSuggestion(BaseModel):
    missing_element: str  = Field(description="Kya cheez missing hai? (e.g., Differential Diagnosis, Risk factor)")
    suggested_text: str = Field(description="Doctor ke liye tayyar shuda professional medical line jo wo add kar sakta hai")
    legal_justification: str = Field(description="Kyun ye line add karna zaroori hai (CMS guidelines)")
    potential_revenue_impact: str = Field(description="Is line se kitne paise bach sakte hain ya barh sakte hain")

class CDIResponse(BaseModel):
    original_score: float
    optimized_score_prediction: float = Field(description="Agar doctor ye lines add kare toh score kya hoga")
    suggestions: List[ImprovementSuggestion]
    addendum_template: str = Field(description="Pura note jo doctor 'copy-paste' kar sake as an addendum")

class DocumentationOptimizer:
    def __init__(self):
        logger.info("Initializing CDI Optimizer (Clinical Documentation Improvement)...")
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"

    async def generate_improvements(
        self, 
        original_note: str, 
        audit_findings: List[Dict],
        current_score: float
    ) -> CDIResponse:
        
        """
        Auditor ki report dekh kar note behtar karne ka plan banata hai.
        """
        
        system_prompt = """
        You are a Senior CDI (Clinical Documentation Improvement) Specialist with 30 years experience.
        Your goal is to help doctors improve their clinical notes so they are 'Audit-Proof'.

        RULES:
        1. Never invent clinical facts (don't say the patient had a fever if they didn't).
        2. Suggest 'Addendums' based on standard medical practices (e.g., if a drug was given, suggest documenting the risk counseling).
        3. Use professional medical terminology.
        4. Focus on Medical Decision Making (MDM) gaps identified by the auditor.
        """

        user_prompt = f"""
        ORIGINAL NOTE:
        {original_note}

        AUDITOR FINDINGS (GAPS):
        {audit_findings}

        CURRENT COMPLIANCE SCORE: {current_score}

        Task: Provide specific suggestions to bridge the documentation gap. 
        Create a professional 'Addendum' text that the doctor can sign.
        """

        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=CDIResponse,
                temperature=0.3
            )

            return response.choices[0].message.parsed

        except Exception as e:
            logger.error(f"CDI Optimizer Error: {e}")
            raise