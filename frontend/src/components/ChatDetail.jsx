import React, { useState, useRef, useEffect } from 'react';
import Button from './Button/Button';
import { MdSend } from "react-icons/md";
import { useNavigate } from 'react-router-dom';
import { AiOutlinePaperClip } from "react-icons/ai";
import { GrLogout } from "react-icons/gr";
import { MdOutlineNotStarted } from "react-icons/md";

function ChatDetail() {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const inputRef = useRef(null);
  const [typing, setTyping] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch chat history from Flask backend on component mount
    fetch('/chat')
      .then(response => response.json())
      .then(data => {
        if (data.chat_history) {
          setMessages(data.chat_history);
        }
      })
      .catch(error => console.error('Error fetching chat history:', error));
  }, []);

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      // Send message to Flask backend
      fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 'user-message': newMessage.trim() }),
      })
        .then(response => response.json())
        .then(data => {
          console.log('Response from server:', data);
          if (data.response) {
            setMessages(prevMessages => [...prevMessages, { question: newMessage.trim(), response: data.response, source: data.source_file_names }]);
            setNewMessage('');
            inputRef.current.focus();
            setIsSending(true);
            // Simulate a send message action
            setTimeout(() => {
              console.log("Message sent!");
              setIsSending(false); // Reset to typing state after sending
            }, 1000);
          }
        })
        .catch(error => console.error('Error sending message:', error));
    }
  };

  const handleInputChange = () => {
    setTyping(inputRef.current.value.length > 0);
  };

  const handleClick = () => {
    navigate('/upload'); 
};

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleSendMessage();
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch('/logout', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        navigate('/');
      } else {
        console.error('Logout failed');
      }
    } catch (error) {
      console.error('An error occurred during logout', error);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Contact nav */}
      <div className="flex justify-between bg-[#212121] h-[60px] p-3">
        {/* Contact info */}
        <div className="flex items-center">
          <div className="flex flex-col">
            <h1 className="text-white font-sm text-[20px] my-2">PdfChat</h1>
          </div>
          <div className="absolute top-0 right-0 m-4*">
            <Button icon={<GrLogout />} onClick={handleLogout} />
          </div>
        </div>
      </div>

      {/* Messages section */}
      <div className="overflow-y-scroll h-screen flex justify-center" style={{ padding: "12px 7%" }}>
        <div>
          {messages.map((msg, index) => (
            <div key={index}>
              <div className="flex items-start">
                <div className="rounded-xl bg-2f2f2f text-white p-4 sm:max-w-md md:max-w-2xl">
                  <p>{msg.question}</p>
                </div>
              </div>
              <div className="flex flex-row-reverse items-start mt-2">
                <div className="rounded-xl bg-green-200 text-white p-4 dark:bg-slate-800 sm:max-w-md md:max-w-2xl">
                  <p>{msg.response}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom section */}
      <div className="flex items-center justify-center p-2">
        <span className="mr-2">
          <Button icon={<AiOutlinePaperClip onClick={handleClick}/>} />
        </span>

        <input
          type="text"
          placeholder="Type a message"
          className="bg-[#333333] rounded-full outline-none text-sm text-neutral-200 w-50 h-100 px-3 placeholder:text-sm placeholder:text-[#8796a1]"
          value={newMessage}
          onChange={(e) => { setNewMessage(e.target.value); handleInputChange(e) }}
          onKeyDown={handleKeyDown}
          ref={inputRef}
        />
        <span className="ml-2">
          {isSending ? (
            <Button
              icon={<MdOutlineNotStarted />}
              disabled
              className={`w-8 h-8 mr-2 rounded bg-green-500`}
            />
          ) : (
            <Button
              icon={<MdSend />}
              onClick={handleSendMessage}
              disabled={!typing}
              className={`w-8 h-8 mr-2 ${!typing ? 'opacity-50 cursor-not-allowed' : 'opacity-100 cursor-pointer'}`}
            />
          )}
        </span>
      </div>
      <div className='flex justify-center items-center'>
        <p className='text-[12px] text-[#545454]'>This is powered by DXC Technology Team</p>
      </div>
    </div>
  );
}

export default ChatDetail;
