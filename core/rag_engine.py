import os
import pickle
import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger
from typing import List, Dict

class RAGEngine:
    def __init__(self,model_name:str="all-MiniLM-L6-v2"):
        logger.info(f"Initializing RAG Engine with model: {model_name}")
        self.model=SentenceTransformer(model_name)
        self.index=None
        self.metadata=[]
        self.db_path="data/vector_db/"

    def create_vector_db(self,csv_path:str,text_column:str):

        if not os.path.exists(csv_path):
            logger.error(f"File {csv_path} not found.")
            return
        logger.info(f"Loading {csv_path} file...")
        df=pd.read_csv(csv_path).fillna("")
        records=df.to_dict("records")
        texts=[str(r[text_column])for r in records]
        embeddings=self.model.encode(texts,show_progress_bar=True)
        dimensions=embeddings.shape[1]
        self.index=faiss.IndexFlatL2(dimensions)
        self.index.add(np.array(embeddings).astype("float32"))
        self.metadata=records
        logger.info(f"Vector DB created successfully.")









    



    def save_to_disk(self,file_name:str="medical_knowledge"):
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path,exist_ok=True)
        index_file=os.path.join(self.db_path,f"{file_name}.index")
        metadata_file=os.path.join(self.db_path,f"{file_name}.metadata")
        faiss.write_index(self.index,index_file)
        with open(metadata_file,"wb") as f:

            pickle.dump(self.metadata,f)


        logger.success(f"Database permanently saved at {self.db_path}")





    def load_from_disk(self,file_name:str="medical_knowledge"):
        index_file=os.path.join(self.db_path,f"{file_name}.index")
        metadata_file=os.path.join(self.db_path,f"{file_name}.metadata")

        if  os.path.exists(index_file) and os.path.exists(metadata_file):
            self.index=faiss.read_index(index_file)
            with open(metadata_file,"rb") as f:
                self.metadata=pickle.load(f)
                logger.success(f"Database loaded from {self.db_path}")
                return True
        else:
            logger.error(f"Database not found at {self.db_path}")


    def search_relevant_codes(self,clinical_note:str,top_k:int=5)->List[str]:
        if self.index is None:
            logger.error("Vector DB not found. Please create one first.")
            return []
        query_vector=self.model.encode([clinical_note])
        distances,indices=self.index.search(np.array(query_vector).astype("float32"),top_k)
        results=[]
        for i in range(len(indices[0])):
            idx=indices[0][i]
            if idx != -1:
                res=self.metadata[idx].copy()
                res['confidence_score']=round(float(distances[0][i]),4)
                results.append(res)
            return results



if __name__ == "__main__":
    rag = RAGEngine()
    

    if not rag.load_from_disk():



        pass



