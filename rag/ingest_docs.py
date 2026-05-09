import os 
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid



class document_ingestor():
    """
    Class to ingest documents and store them into qdrant vector database.
    
    """
    
    INPUT_FOLDER = r"../data/documents"
    EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
    QDRANT_URL = "http://localhost:6333"
    COLLECTION_NAME = "Vector_collection_cyber_docs"

    
    
    Document_Text_Dictionary = {}
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    qdrant = QdrantClient(url=QDRANT_URL)
    
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len
    )
    ## read in each docuemnts data store as key : value pair document name : text
    def extractText(self):
        """
        The text splitter we use later for .create_documents requires 1 long string not an array
        therfore here we have an array of text page numbner combos we will break down later
        """
        data_dict = {}
        for filepath in os.listdir(self.INPUT_FOLDER):
            filepath = os.path.join(self.INPUT_FOLDER, filepath)
            with(open(filepath, "r") as f):
                reader = PdfReader(filepath)
                filename = os.path.basename(filepath)
                texts = []
                for page_number, page in enumerate(reader.pages):
                    texts.append({"text": page.extract_text(), "page_number": page_number + 1})
                    #print(str({texts[0]["text"]}), int(texts[0]["page_number"]))
                data_dict[filename] = texts ## each file has entry of text: texts, pagenum: number
                    
        
        return data_dict
                
    
    def chunk_docs(self, Dictionary):
        """
        Langhchain expects list of length 1 with a string, if we pass just data to create_documents it 
        treats data as an intterable so hello = ['h', 'e', 'l', 'l', 'o'].
        """
        total_chunks = []
        for filename, data in Dictionary.items(): 
            for entry in data:
                text = str(entry["text"])
                page_number = int(entry["page_number"])
                print(f"\n text: {text} at page: {page_number}")
                
                chunks = self.text_splitter.create_documents(
                    texts=[entry["text"]], 
                    metadatas=[{"source": filename, "page_number": page_number}])
                total_chunks.extend(chunks)
        
        return total_chunks
    
    
    def create_qdrant_collection(self):
        """Create a collection to store the vector data
        """
        if self.qdrant.collection_exists(collection_name=self.COLLECTION_NAME):
            print(f"collection {self.COLLECTION_NAME} already exists")
            return
        
        self.qdrant.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.DOT) # since our embeddingsa model is 768 dimensional vectors
        )
        
        
    
    def create_embeddings(self, chunks_Dataset):
        """
        Create the embeddings which we store with the meta data of that chunk into a "point". "points" are the central entity
        that Qdrant operates with according to their website. A point consits of a vector and optional payload

        Args:
            chunks (array of langchain document structures): contains chunks of text with meta data of filename and pagenumber for each chunk
            chunk[0].page_content is the chunk of text
            chunk[0].metadata["page_number"] is page num of chunk and 
            chunk[0].metadata["source"] is the filename
        """
        

        ## extract all chunks into sublist
        ## get vector output for sublist
        ## itterate over chunks
        # for each chunk we get the page num the source, the page content and the vector embedding
        # into qdrant db we store payload as page content (chunk text), page number, document source and the vector as the vector
        chunks = [chunk.page_content for chunk in chunks_Dataset]
        vectors = self.embedder.encode(chunks)
        points=[]
        
        ## for every chunk we create an array of pointstructs with the ID, vector, and payload
        points = [ PointStruct(id = uuid.uuid4(),
                               vector = vectors[index], 
                               payload={
                                   "chunksource": chunk.metadata["source"], 
                                    "pagenumber": chunk.metadata["page_number"], 
                                    "chunktext": chunk.page_content
                                }) for index, chunk in enumerate(chunks_Dataset)]
       
    
                
        operation_info = self.qdrant.upsert(
            collection_name=self.COLLECTION_NAME,
            wait=True,
            points=points,
        )
        
        print(operation_info)
        
        
def main():
    DI = document_ingestor()
    Dictionary = DI.extractText()
    Chunks = DI.chunk_docs(Dictionary)
    
    for var in Chunks:
        print(f"\n, {var.page_content} at page {var.metadata["page_number"]}")
        break
    
    DI.create_qdrant_collection()
    DI.create_embeddings(Chunks)
    
if __name__ == "__main__":
    main()
    