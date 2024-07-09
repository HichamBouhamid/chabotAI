import streamlit as st
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.docstore.document import Document
from pymongo import MongoClient
from gridfs import GridFS
from PyPDF2 import PdfReader

load_dotenv()

os.environ['OPENAI_API_KEY']=os.getenv("OPENAI_API_KEY")

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['rag_system_04042024']
fs = GridFS(db)

def setup_environment_and_db():
    #chunks = db["chunks"]
    #conversation = db["conversation"]
    List_docs = db["List_docs"]
    return List_docs


#def get_pdf_text(pdf_docs):
#    text=""
#    for pdf in pdf_docs:
#        pdf_reader= PdfReader(pdf)
#        for page in pdf_reader.pages:
#            text+= page.extract_text()
#    return  text

def get_pdf_text(pdf_docs):
    documents = []
    for pdf in pdf_docs:
        pdf_reader= PdfReader(pdf)
        for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                metadata = {
                    "source": pdf.name,
                    "page_number": page_num,
                    "total_pages": len(pdf_reader.pages)
                }
                document = Document(page_content=text, metadata=metadata)
                documents.append(document)
        split_documents = get_text_chunks (documents)
        push_on_db(split_documents , pdf.name , pdf)
        documents = []






def get_text_chunks(documents, chunk_size=10000, chunk_overlap=1000):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap ,  add_start_index=True )# Set this to True
    # Concatenate all page contents into a single text
    full_text = "".join(doc.page_content for doc in documents)

    # Split the full text using RecursiveCharacterTextSplitter
    splits = text_splitter.create_documents([full_text])

    # Create new Document objects with split text and page metadata
    split_documents = []

    for split_id, split in enumerate(splits):
        # Find the pages that this split text spans
        start_idx = split.metadata.get("start_index", 0) 
        end_idx = start_idx + len(split.page_content)
        page_indices = []
        doc_cumul = 0
        for i, doc in enumerate(documents):
            doc_start = doc_cumul
            doc_cumul += len(doc.page_content)
            doc_end = doc_cumul
            if (doc_start >= start_idx and doc_start < end_idx) or (doc_end > start_idx and doc_end <= end_idx):
                page_indices.append(doc.metadata["page_number"])
        # Create a new Document with split text and page metadata
        metadata = {"page_indices": page_indices, "split_id": split_id, "source": documents[0].metadata["source"]}
        split_doc = Document(page_content=split.page_content, metadata=metadata)
        split_documents.append(split_doc)

    return split_documents


def push_on_db(split_documents , doc_name ,pdf):
    embeddings  = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(split_documents, embedding=embeddings )
    vector_store.save_local("faiss_index")

    # Convert split documents to a format suitable for MongoDB
    collection_doc_name = "M_" + doc_name
    users_collection = db[collection_doc_name]

    mongo_docs = []
    for doc in split_documents:
        embedding = embeddings.embed_query(doc.page_content)
        mongo_doc = {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "embedding": embedding  # Convert embedding to a list for MongoDB
        }
        mongo_docs.append(mongo_doc)

    # Insert the documents into MongoDB
    users_collection.drop()
    users_collection.insert_many(mongo_docs)
    file_id = fs.put(pdf, filename=doc_name, content_type="application/pdf")
    List_docs = db["List_docs"]
    List_docs.find_one_and_update({ "filename": doc_name },
                                  {"$set": {"filename": doc_name, 
                                            "collection_doc_name": collection_doc_name, 
                                            "GridFS_file_id": file_id}},
                                   upsert=True)



def get_conversational_chain():

    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatOpenAI(temperature=0)

    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain



def user_input(user_question, pdf_docs_for_search):
    embeddings = OpenAIEmbeddings()
    
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    filtered_docs = []
    for pdf_doc in pdf_docs_for_search:
        # Use metadata from the document or define metadata criteria as needed
        metadata = {"source": pdf_doc.filename}  # Example metadata criteria
        filtered_docs.extend(new_db.filter_by_metadata(metadata, pdf_doc))
         
    chunks = new_db.similarity_search(user_question, documents=filtered_docs)
    print(chunks)
    chain = get_conversational_chain()

    response = chain(
        {"input_documents":chunks, "question": user_question}
        , return_only_outputs=False)

    print(response)
    st.write("Reply: ", response["output_text"])



pdf_docs_for_search = []
def main():
    List_docs = setup_environment_and_db()
    st.set_page_config("Chat PDF")
    st.header("Chat with PDF using open ai💁")

    user_question = st.text_input("Ask a Question from the PDF Files")

    if user_question:
        user_input(user_question , pdf_docs_for_search)


    with st.sidebar:
        st.title("Menu:")
        st.subheader("Upload new documents")
        pdf_docs = st.file_uploader("Upload new PDFs here:", accept_multiple_files=True)
        
        if st.button("Load doc") and pdf_docs:
            with st.spinner("Processing..."):
                get_pdf_text(pdf_docs)
                List_docs = setup_environment_and_db()
                existing_files = [doc["filename"] for doc in List_docs.find({}, {"filename": 1})]
                st.success("Document(s) successfully loaded.")

        st.subheader("Or select existing documents")
        List_docs = setup_environment_and_db()  
        
        existing_files = [doc["filename"] for doc in List_docs.find({}, {"filename": 1})]
        selected_files = st.multiselect("Select documents to ask questions about:", existing_files)


        
        for selected_file in selected_files:
            pdf_docs_for_search.append(List_docs.find_one({"filename": selected_file}))

if __name__ == "__main__":
    main()