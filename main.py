from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import logging
from pymongo import MongoClient
from gridfs import GridFS
from datetime import datetime
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from bson import ObjectId
import os
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
import hashlib, secrets
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)
os.environ['OPENAI_API_KEY']=os.getenv("OPENAI_API_KEY")

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['rag_system_04042024']
fs = GridFS(db)

#This functios is used to setup the environment & the database
def setup_environment_and_db():
    List_docs = db["List_docs"] 
    users_collection = db['users'] 
    chat_collection = db['chat'] 
    return List_docs,users_collection,chat_collection

app = Flask(__name__)

secret_key = secrets.token_hex(16)
app.secret_key = secret_key.encode('utf-8')

def get_pdf_text(pdf_docs):
    documents = []
    for pdf in pdf_docs:   
        file_name = pdf.filename
        pdf_reader = PdfReader(pdf)
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            text = page.extract_text()
            metadata = {
            "source": file_name,
            "page_number": page_num,
            "total_pages": len(pdf_reader.pages)
            }
            document = Document(page_content=text, metadata=metadata)
            documents.append(document)
        split_documents = get_text_chunks(documents)
        push_on_db(split_documents, file_name, pdf)
        

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


def push_on_db(split_documents, doc_name, pdf):
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(split_documents, embedding=embeddings)
    vector_store.save_local("faiss_index")

    collection_doc_name = "M_" + doc_name
    users_collection = db[collection_doc_name]

    mongo_docs = []
    for doc in split_documents:
        embedding = embeddings.embed_query(doc.page_content)
        mongo_doc = {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "embedding": embedding
        }
        mongo_docs.append(mongo_doc)
    
    users_collection.drop()
    users_collection.insert_many(mongo_docs)
    
    # Store the file in GridFS and get the file_id
    file_id = fs.put(pdf, filename=doc_name, content_type="application/pdf")
    List_docs = db["List_docs"]
    user_id = session.get('_id')
    
    # Ensure the file_id is stored correctly
    List_docs.find_one_and_update(
        {"filename": doc_name},
        {"$set": {"filename": doc_name, "GridFS_file_id": file_id, "user_id": user_id}},
        upsert=True
    )

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def user_input(user_question, pdf_docs_for_search,memory):
    embeddings = OpenAIEmbeddings()
    
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    filtered_docs = []
    for pdf_doc in pdf_docs_for_search:
        # Use metadata from the document or define metadata criteria as needed
        metadata = {"source": pdf_doc.filename}# Example metadata criteria
        filtered_docs.extend(new_db.filter_by_metadata(metadata, pdf_doc))
    
    chunks = new_db.similarity_search(user_question, documents=filtered_docs)
    vectorstore1 = FAISS.from_documents(chunks, embedding=embeddings )
    #memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    model = ChatOpenAI(temperature=0)
    chain = ConversationalRetrievalChain.from_llm(
    llm=model,
    chain_type="stuff",
    retriever=vectorstore1.as_retriever(search_kwargs={"k": 2}),
    memory=memory,
    output_key='answer'
    )
    response = chain({"question": user_question})
    source_file_names = [chunk.metadata.get("source") for chunk in chunks]
    return response, source_file_names

def read_document_from_db(file_id):
    try:
        file_id = ObjectId(file_id)  # Convert to ObjectId
        document = fs.find_one({"_id": file_id})
        if document is not None:
            content_type = document.content_type
            if content_type == "application/pdf":
                file_bytes = document.read()
                pdf_stream = io.BytesIO(file_bytes)
                pdf_reader = PdfReader(pdf_stream)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
            else:
                return "Unsupported file type"
        else:
            logging.warning(f"Document not found for file_id: {file_id}")
            return "Document not found"
    except Exception as e:
        logging.error(f"Exception in read_document_from_db: {str(e)}")
        return "Error reading document"

    
#This function is used to turn the list of documents stored in the database 
def get_stored_documents():
    return db.List_docs.find()
    
List_docs,users_collection,chat_collection = setup_environment_and_db()    
pdf_docs_for_search = []
stored_documents = get_stored_documents()
# Check if user is logged in
def is_logged_in():
    return 'username' in session

@app.route('/')
def index():
    if not is_logged_in(): #If the user isn't logged in he'll be redirected to login page else to index.html page and
        return jsonify({'message': 'LogIn'}), 200 
    else:
       return jsonify({'message': 'Done.'}), 401 

@app.route('/upload', methods=['POST'])
def upload_pdf():
        pdf_docs = request.files.getlist('file') #Get the list of files uploaded 
        if pdf_docs:
            # Call get_pdf_text() to process the uploaded files and get the documents
            documents = get_pdf_text(pdf_docs)
            List_docs = setup_environment_and_db()
            return jsonify({'message': 'Successfully Uploaded'}), 200 
        else:
            return jsonify({'message': 'Error'}), 401 
                 
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_id = session.get('_id')  # Get the user_id from the session
        user_question = request.json['user-message']  # Get JSON data from request body

        # Perform any necessary processing with the user question here
        response, source_file_names = user_input(user_question, pdf_docs_for_search, memory)
        response1 = response["answer"]

        # Check if a document for this user exists
        user_chat = chat_collection.find_one({"user_id": user_id})
        
        if not user_chat:
            # If no chat history exists for this user, create a new document
            user_chat = {
                'user_id': user_id,
                'question': user_question,
                'timestamp': datetime.utcnow(),
                'chat_history': []     
            }
            chat_insert_result = chat_collection.insert_one(user_chat)
            chat_id = chat_insert_result.inserted_id
        else:
            chat_id = user_chat['_id'],
            
        # Append the new message and response to the chat history with timestamp
        chat_collection.update_one(
            {'user_id': user_id},
            {'$push': {'chat_history': {
                'question': user_question,
                'response': response1,
                'source': source_file_names
            }}}
        )
        # Return the response to the frontend, including the chat_id
        return jsonify({'response': response1, 'source_file_names': source_file_names, 'chat_id': str(chat_id)})
    else:
        # Retrieve user_id from the session
        user_id = session.get('_id')
        if user_id:
            # Query chat_collection for the user's chat document
            user_chat = chat_collection.find_one({"user_id": user_id})
            if user_chat:
                chat_history = user_chat['chat_history']
                return jsonify({'chat_history': chat_history, 'chat_id': str(user_chat['_id'])})
            else:
                return jsonify({'chat_history': []})
        else:
            return jsonify({'error': 'User ID not found in session'}), 401
        
@app.route('/get_chat_questions', methods=['GET'])
def get_chat_questions():
    user_id = session.get('_id')  # Get the user_id from the session

    # Find the chat history for the given user
    user_chat = chat_collection.find_one({"user_id": user_id})

    if not user_chat:
        return jsonify({'question': 'No question found for this user'})

    # Get the latest question and timestamp from the chat history
    latest_question = user_chat.get('question', 'No question found')
    timestamp = user_chat.get('timestamp', datetime.utcnow())

    return jsonify({'question': latest_question, 'timestamp': timestamp})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    user_id = session.get('_id')  # Get the user_id from the session
    timestamp = datetime.utcnow()

    # Create a new chat object
    new_chat = {
        'user_id': user_id,
        'timestamp': timestamp,
        'chat_history': []
    }

    # Insert the new chat object into the chat collection
    chat_insert_result = chat_collection.insert_one(new_chat)
    new_chat_id = chat_insert_result.inserted_id

    return jsonify({'message': 'New chat created', 'chat_id': str(new_chat_id)})

@app.route('/get_documents', methods=['GET'])
def get_stored_documents():
    documents = db.List_docs.find()
    document_list = [{'id': str(doc['_id']), 'filename': doc['filename']} for doc in documents]
    return jsonify(document_list)

@app.route('/read_document/<file_id>', methods=['GET'])
def read_document(file_id):
    try:
        # Log the received file_id
        logging.info(f"Received file_id: {file_id}")

        # Call the function to read the document
        document_text = read_document_from_db(file_id)
        logging.info(f"Document text: {document_text}")

        return jsonify({'document_text': document_text}), 200
    except Exception as e:
        logging.error(f"Error reading document: {str(e)}")
        return jsonify({'error': 'Failed to read document'}), 500
            
#This is register router
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        # Getting the data filled in the register form
        data = request.json
        
        if data:
            # Extracting data from JSON
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            
            if not username or not password or not email:
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Check if username & email already exist in the database
            if users_collection.find_one({'email': email, 'username': username}):
                return jsonify({'error': 'User already exists!'}), 400
            else: 
                # Hash password
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                
                # Insert user into user_collection 
                users_collection.insert_one({'username': username, 'password': hashed_password, 'email': email})
                
                return jsonify({'message': 'Registration successful'}), 200
        else:
            return jsonify({'error': 'No data received'}), 400
    


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.json
        if data:
            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return jsonify({'error': 'Missing required fields'}), 400

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            user = users_collection.find_one({'username': username, 'password': hashed_password})
            if user:
                session['username'] = user['username']
                session['_id'] = str(user['_id'])  # Ensure ObjectId is converted to string
                return jsonify({"message": "Login successful"}), 200
            else:
                return jsonify({"error": "Invalid username or password"}), 401
        else:
            return jsonify({'error': 'No data received'}), 400
    
@app.route('/delete', methods=['POST'])
def delete_user():
    user_id = session.get('_id')
    if user_id:
        # Convert the string user_id to ObjectId
        user_id = ObjectId(user_id)

        # Find the user by their unique ID
        user = users_collection.find_one({'_id': user_id})
        if user:
            # Delete the user from the collection
            users_collection.delete_one({'_id': user_id})
            # Clear the session
            session.clear()
            return 'User deleted'
    else:
            return 'User not found!'


@app.route('/update', methods=['GET', 'POST'])
def update_user():
    user_id = session.get('_id')
    if not user_id:
        return 'No user logged in!'

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        update_fields = {}
        if username:
            update_fields['username'] = username
        if email:
            update_fields['email'] = email
        if password:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            update_fields['password'] = hashed_password

        if update_fields:
            users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_fields}
            )
            return redirect('chat')
        else:
            return 'No fields to update!'
    else:
        return render_template('update_user.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)  # Clear session
    return jsonify({'message': 'Logged out successfully'}), 200 

if __name__ == '__main__':
    app.run(debug=True)