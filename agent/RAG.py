import os
import shutil
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class LocalRAGAgent:
    def __init__(self, pdf_path=None, base_folder="local_rag", multi_process=False):
        self.base_folder = base_folder
        self.db_folder = os.path.join(base_folder, "vector_store")
        self.pdf_storage = os.path.join(base_folder, "pdf_files")
        self.model_name = "BAAI/bge-m3"
        self.docs = [] # Inicializamos para evitar errores
        
        # Configuración para Ryzen 7 PRO 250
        os.environ["OMP_NUM_THREADS"] = "8"
        
        os.makedirs(self.db_folder, exist_ok=True)
        os.makedirs(self.pdf_storage, exist_ok=True)

        # CORRECCIÓN: Quitamos 'show_progress_bar' de encode_kwargs para evitar el duplicado
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={
                'batch_size': 64, 
                'normalize_embeddings': True
            },
            show_progress=True, # LangChain lo maneja desde aquí
            multi_process=multi_process 
        )
        
        self.vector_store = None
        
        if pdf_path:
            self.add_new_pdf(pdf_path)
        else:
            self.load_or_build_from_folder()

    def load_or_build_from_folder(self):
        pdf_files = glob.glob(os.path.join(self.pdf_storage, "*.pdf"))
        
        if not pdf_files:
            print(f"⚠️ No hay archivos PDF en {self.pdf_storage}.")
            return

        if os.path.exists(os.path.join(self.db_folder, "chroma.sqlite3")):
            print(f"⚡ Cargando base de datos existente...")
            self.vector_store = Chroma(
                persist_directory=self.db_folder,
                embedding_function=self.embeddings
            )
            # Cargamos el primer PDF a memoria para que return_by_page funcione
            loader = PyPDFLoader(pdf_files[0])
            self.docs = loader.load()
        else:
            print(f"🚀 Creando base de datos desde cero...")
            all_chunks = []
            for pdf in pdf_files:
                all_chunks.extend(self._process_pdf(pdf))
            
            self.vector_store = Chroma.from_documents(
                documents=all_chunks,
                embedding=self.embeddings,
                persist_directory=self.db_folder
            )

    def _process_pdf(self, path):
        loader = PyPDFLoader(path)
        docs = loader.load()
        self.docs = docs # Guardamos los documentos cargados
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        return text_splitter.split_documents(docs)

    def add_new_pdf(self, pdf_path):
        pdf_filename = os.path.basename(pdf_path)
        dest_path = os.path.join(self.pdf_storage, pdf_filename)
        
        if not os.path.exists(dest_path):
            shutil.copy(pdf_path, dest_path)
        
        chunks = self._process_pdf(dest_path)
        
        if self.vector_store is None:
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.db_folder
            )
        else:
            self.vector_store.add_documents(chunks)
        print(f"✅ {pdf_filename} indexado.")

    def search(self, query, k=3):
        if not self.vector_store:
            return []
        results = self.vector_store.similarity_search(query, k=k)
        return [{
            "texto": doc.page_content,
            "pagina": doc.metadata.get('page', 0) + 1,
            "archivo": os.path.basename(doc.metadata.get('source', 'desconocido')),
        } for doc in results]

    def return_by_page(self, pages: list[int]):
        """Devuelve un diccionario con el texto de cada página solicitada."""
        result = {}
        if not self.docs:
            return {"error": "No hay documentos cargados en memoria."}
            
        for page in pages:
            # Validación simple para no salirnos del rango del PDF
            if 0 <= page < len(self.docs):
                result[str(page + 1)] = self.docs[page].page_content
            else:
                result[str(page + 1)] = "Página fuera de rango."
        return result

if __name__ == "__main__":
    # Importante: multi_process=False para evitar errores de bootstrapping en búsquedas rápidas
    rag = LocalRAGAgent("main_notes.pdf", multi_process=False)
    resultados = rag.search("explicación de SVM", k=2)
    
    for res in resultados:
        print(f"\n[{res['archivo']}]: {res['texto'][:200]}...")