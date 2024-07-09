import React, { useState, useEffect } from 'react';
import Button from './Button/Button';
import { IoMenu } from 'react-icons/io5';
import { AiOutlineWechatWork } from 'react-icons/ai';
import { BiFilter } from 'react-icons/bi';
import { useNavigate } from 'react-router-dom';

function LeftMenu() {
  const [filter, setFilter] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [questionsWithDates, setQuestionsWithDates] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [documentText, setDocumentText] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    // Fetch documents from Flask backend
    fetch('/get_documents')
      .then(response => response.json())
      .then(data => {
        setDocuments(data);
      })
      .catch(error => console.error('Error fetching documents:', error));

    // Fetch chat questions with dates from Flask backend
    fetch('/get_chat_questions', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Include cookies in the request
    })
      .then(response => response.json())
      .then(data => {
        if (data.question) {
          setQuestionsWithDates([{ question: data.question, date: data.timestamp }]);
        } else {
          console.error('No question found for this user');
        }
      })
      .catch(error => console.error('Error fetching chat questions:', error));
  }, []);

  const handleNewChat = () => {
    // Make a POST request to create a new chat object
    fetch('/new_chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Include cookies in the request
    })
      .then(response => {
        if (response.ok) {
          // If the chat session is created successfully, clear the chat history
          navigate('/chat', { replace: true }); // Replace the current URL with the chat page URL
          setDocuments([]);
        } else {
          console.error('Failed to create chat session');
        }
      })
      .catch(error => console.error('Error creating chat session:', error));
  };

  const fetchDocument = async (fileId) => {
    try {
      const response = await fetch(`/read_document/${fileId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDocumentText(data.document_text);
        console.log('Document Text:', data.document_text);
      } else {
        const errorData = await response.json();
        console.error('Error:', errorData.error);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  return (
    <div className="flex flex-col border-r border-neutral-700 w-100 h-screen">
      {/* Profile nav */}
      <div className="flex justify-between items-center h-[60px] p-3">
        <Button icon={<IoMenu />} />
        <div className='flex justify-between'>
          <Button icon={<AiOutlineWechatWork />} onClick={handleNewChat} />
        </div>
      </div>
      <div className='flex justify-between items-center h-[60px] p-2'>
        <input
          type="text"
          placeholder='Search or start a new Chat'
          className='rounded-lg bg-[#202d33] text-[#8796a1] text-sm font-light outline-none p-2 px-4 py-2 w-[400px] h-[35px] placeholder:text-[#8796a1] placeholder:text-sm placeholder:font-light' />
        {/* Filter button */}
        <button
          className={`text-2xl m-2 p-1 rounded-full ${filter
            ? "bg-emerald-500 text-white rounded-full hover:bg-emerald-700"
            : "text-[#8796a1] hover:bg-[#3c454c]"
            }`}
          onClick={() => setFilter(!filter)}
        >
          <BiFilter />
        </button>
      </div>
      {/* Prompt history panel */}
      <div className="flex my-4 mx-3">
        <h1 className="text-[20px] text-white ">
          Chat History
        </h1>
      </div>

      <div className="h-80 space-y-4 overflow-y-auto px-2">
        {questionsWithDates.map((entry, index) => (
          <button
            key={index}
            className="flex w-full flex-col gap-y-2 rounded-lg px-3 py-2 text-left transition-colors duration-200 hover:bg-slate-200 focus:outline-none dark:hover:bg-slate-800"
          >
            <h1 className="text-sm font-medium capitalize text-slate-700 dark:text-slate-200" style={{ whiteSpace: 'nowrap' }}>
              {entry.question}
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {entry.date}
            </p>
          </button>
        ))}
      </div>
      <div className='flex justify-center items-center'>
        <select
          id="documents"
          name="document_id"
          className=" bg-gray-50 border border-gray-300 text-gray-900 w-[200px] text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
          value={selectedDocumentId} // Use value prop instead of defaultValue
          onChange={(e) => setSelectedDocumentId(e.target.value)} // Handle change event
        >
          <option value="" disabled>Select a document</option>
          {documents.map(document => (
            <option key={document.id} value={document.id}>{document.filename}</option>
          ))}
        </select>

      </div>
      <button
        onClick={() => {
          if (selectedDocumentId) {
            fetchDocument(selectedDocumentId);
          } else {
            console.error("No document selected");
          }
        }}
        className="block mx-auto mt-8 px-5 py-2.5 bg-purple-700 text-white text-center text-base font-bold rounded-md hover:bg-blue-700"
      >
        Load
      </button>

      {documentText && (
        <div className="p-4 mt-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Document Content:</h2>
          <p className="text-gray-700 dark:text-gray-300">{documentText}</p>
        </div>
      )}
    </div>
  );
}

export default LeftMenu;
