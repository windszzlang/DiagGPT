from typing import Sequence, List, Union

from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, UnstructuredMarkdownLoader
from langchain.document_loaders.image import UnstructuredImageLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import NLTKTextSplitter, TextSplitter
from langchain.vectorstores import VectorStore, OpenSearchVectorSearch
import nltk
nltk.download('punkt')


_default_text_splitter = NLTKTextSplitter.from_tiktoken_encoder(
    separator="\n\n",
    chunk_size=500,
    # chunk_size=600,
    chunk_overlap=100,
)


def get_vectorstore(opensearch_url: str, index_name: str, http_auth: tuple):
    embeddings = OpenAIEmbeddings()
    return OpenSearchVectorSearch(opensearch_url=opensearch_url, embedding_function=embeddings, index_name=index_name,
                                  engine="faiss", space_type="cosinesimil", ef_construction=256, m=48,
                                  text_field='text', vector_field='vector_field', http_auth=http_auth)


class Embedder:
    """Embeds pdf and saves it into a vector store.
    """

    def __init__(self, vectorstore: VectorStore):
        self.vectorstore = vectorstore

    def file2docs(self, file_path: str, text_splitter: TextSplitter = None) -> Sequence[Document]:
        """Loads a Word and splits it into documents.

        Args:
            file_path (str): Path to the PDF / word / image file.
            text_splitter (TextSplitter, optional): Method to split text. Defaults to None.

        Returns:
            Sequence[Document]: List of documents.
        """
        if text_splitter is None:
            text_splitter = _default_text_splitter
        
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.doc') or file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        # elif file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg') or file_path.lower().endswith('.png'):
            # loader = UnstructuredImageLoader(file_path)
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path)
        elif file_path.endswith('.md'):
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            return None
        docs = loader.load_and_split(text_splitter=text_splitter)
        return docs

    @staticmethod
    def embed_text(text: str) -> List[float]:
        """Embeds text into a vector.

        Args:
            text (str): Text to be embedded.

        Returns:
            List[float]: Vector representation of the text.
        """
        embeddings = OpenAIEmbeddings()
        return embeddings.embed_query(text)

    def save(self, docs: Union[Sequence[Document], Document]) -> List[str]:
        """Saves documents into the vector store.

        Args:
            docs (Union[Sequence[Document], Document]): Documents to be saved.

        Returns:
            List[str]: List of IDs from adding the texts into the vector store.
        """
        if isinstance(docs, Document):
            docs = [docs]
        for d in docs:
            # TODO: Avoid duplicate insertion
            self.vectorstore.add_documents([d])
            # self.vectorstore.add_texts([d])

    def search(self, query: str, top_k: int = 4) -> List[Document]:
        """Searches for similar documents in the vector store.

        Args:
            query (str): Query text.
            top_k (int, optional): Number of results to return. Defaults to 4.

        Returns:
            List[Document]: List of similar documents.
        """
        results = self.vectorstore.similarity_search(query, k=top_k)
        return self.limit_doc_length(results)
    
    def limit_doc_length(self, documents: list, word_num=300) -> List[Document]:
        new_documents = []
        for doc in documents:
            doc.page_content = ' '.join(doc.page_content.split(' ')[:word_num])
            new_documents.append(doc)
        return new_documents


if __name__ == "__main__":
    import os

    pdf_path = 'path/to/pdf'
    opensearch_url = os.environ.get('opensearch_url')
    index_name = os.environ.get('index_name', 'test')
    vectorstore = get_vectorstore(opensearch_url, index_name)
    embedder = Embedder(vectorstore)
    docs = embedder.pdf2docs(pdf_path)
    embedder.save(docs)
    print(embedder.search('summary this book'))
