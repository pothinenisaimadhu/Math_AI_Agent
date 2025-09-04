
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from config import QDRANT_URL, QDRANT_COLLECTION, GRANITE_MODEL, OLLAMA_URL, LLAMA_MODEL
from qdrant_client import QdrantClient
import os

class RAGAgent:
    def __init__(self, qdrant_url: str = QDRANT_URL, collection: str = QDRANT_COLLECTION):
        # embeddings
        self.embedder = HuggingFaceEmbeddings(model_name=GRANITE_MODEL)
        # qdrant client
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection = collection
        # LLM via Ollama wrapper
        self.llm = Ollama(model=LLAMA_MODEL, base_url=OLLAMA_URL)
        self.template = """You are a math professor. Use the retrieved context to answer the question in numbered steps.
Context: {context}
Question: {question}
Provide a concise 1-2 line summary and the final answer in LaTeX if appropriate. Mark steps as [sourced] if from context and [derived] otherwise."""
        self.prompt = PromptTemplate(template=self.template, input_variables=["context","question"])

    def get_retriever(self, top_k=5):
        vectordb = Qdrant(client=self.qdrant_client, collection_name=self.collection, embeddings=self.embedder)
        return vectordb.as_retriever(search_kwargs={"k": top_k})

    def answer(self, question: str, top_k: int = 5):
        retriever = self.get_retriever(top_k=top_k)
        qa = RetrievalQA.from_chain_type(llm=self.llm, retriever=retriever, chain_type="stuff", chain_type_kwargs={"prompt": self.prompt})
        return qa.run(question)
