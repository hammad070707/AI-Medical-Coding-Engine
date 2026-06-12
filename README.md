advice
2. Mera Professional Mashwara (Action Plan)
Tumhe 1352 pages ki poori detail Vector DB mein dalne ki zaroorat nahi hai. Hum "Hybrid Approach" use karenge:
Step A: "Flat File" (CSV) dhoondo Codes ke liye
Humein search karne ke liye sirf Code aur Short Description chahiye.
Internet par "CPT 2024 Flat File CSV" ya "CMS CPT/HCPCS data" dhoondo.
Tumhe aik aisi file mil jayegi jis mein sirf 10,000-15,000 rows hongi. Yeh tumhare RAGEngine ke liye perfect hai.
Step B: PDF ko "Knowledge Base" banao (Advanced RAG)
Yeh jo 1352 pages ki PDF hai, isey hum convert nahi karenge. Isey hum "Guidelines" ke taur par use karenge.
Jab Coder Agent koi code suggest karega, toh hum usey is PDF ke relevant pages "Context" ke taur par denge takay wo Rules (jo tum ne upar quote kiye hain) parh kar faisla kare.







2. ICD aur CPT: Ek Vector ya Alag Alag?
Jawab: Alag Alag (Must!)
Ek Senior Architect ki tarah socho:
Agar tum dono ko ek hi file mein daloge, toh search result mix ho jayenge.
Humein icd_knowledge.index alag chahiye aur cpt_knowledge.index alag.
Jab doctor ka note aayega, hum RAG ko bolenge: "Bhai pehle ICD wale index mein Diagnosis dhoondo, phir CPT wale index mein Procedure dhoondo."
3. Modifiers Kahan Gaye?
Bahi, Modifiers ke liye Vector Database nahi banti.
Kyun? Kyunke modifiers (e.g., -LT, -RT, -25) ginti ke 100-150 hain. Inhein AI se "dhoondne" ki zaroorat nahi, balkay inhein "Rules" ke mutabiq lagana parta hai.
Solution: Hum Modifiers ko aik simple modifiers.json file mein rakhenge aur modifier_logic.py mein code likhenge ke: "Agar doctor ne 'Left' likha hai, toh CPT ke saath '-LT' chipka do."
