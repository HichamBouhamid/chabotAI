import React from 'react';
import LeftMenu from '../components/LeftMenu';
import ChatDetail from '../components/ChatDetail';

function ChatPage() {
  return (
    <div className="w-100 h-100 overflow-hidden">
      <div className="flex justify-start chatpdf-bp:justify-center items-center bg-[#000000] h-screen">
        <div className="bg-[#171717] min-w-[250px] max-w-[350px] w-[350px] h-100">
          <LeftMenu />
        </div>
        <div className="bg-[#212121]  min-w-[400px] max-w-screen w-100 h-100">
          <ChatDetail />
        </div>
      </div>
    </div>
  );
}

export default ChatPage;