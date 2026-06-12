from core.rag_engine import RAGEngine
import os

def build_knowledge_base():
    print("--- Building ICD-10 Knowledge Base ---")
    icd_rag=RAGEngine()
    icd_rag.create_vector_db("data/icd10_codes.csv",text_column="Long_Description")
    icd_rag.save_to_disk(file_name="icd10_knowledge")
    print("\n--- Building CPT Knowledge Base ---")
    cpt_rag=RAGEngine()
    cpt_rag.create_vector_db("data/cpt_codes.csv",text_column="label")
    cpt_rag.save_to_disk(file_name="cpt_knowledge")

    print("\nSUCCESS: All Vector Databases created!")

if __name__ == "__main__":
    build_knowledge_base()