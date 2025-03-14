import React, { useState, useRef, useEffect } from 'react';
import { FiSend, FiX, FiMessageSquare } from 'react-icons/fi';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ChatMessage {
  timestamp: string;
  query: string;
  response: string;
}

interface ChatPanelProps {
  jobId: string;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ jobId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [panelWidth, setPanelWidth] = useState(384);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const resizeRef = useRef<HTMLDivElement>(null);
  const [isResizing, setIsResizing] = useState(false);
  const minWidth = 320; 
  const maxWidth = 1200; 

  useEffect(() => {
    if (isOpen) {
      fetchChatHistory();
    }
  }, [isOpen, jobId]);

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const fetchChatHistory = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/jobs/${jobId}/chat`);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      setChatHistory(data.chat_history || []);
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!message.trim()) return;
    
    const currentMessage = message;
    setMessage('');
    setIsLoading(true);
    
    const tempTimestamp = new Date().toISOString();
    const tempChat = {
      timestamp: tempTimestamp,
      query: currentMessage,
      response: '' 
    };
    setChatHistory(prev => [...prev, tempChat]);
    
    try {
      const response = await fetch(`http://localhost:8000/api/jobs/${jobId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: currentMessage }),
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      await response.json();
      fetchChatHistory();
      
    } catch (error) {
      console.error('Error sending message:', error);
      setChatHistory(prev => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        if (lastIndex >= 0) {
          updated[lastIndex] = {
            ...updated[lastIndex],
            response: 'Sorry, there was an error processing your request. Please try again.'
          };
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = window.innerWidth - e.clientX;
      
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setPanelWidth(newWidth);
      }
    };
    
    const handleMouseUp = () => {
      setIsResizing(false);
    };
    
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);
  
  const startResizing = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };
  
  const togglePanel = () => {
    setIsOpen(!isOpen);
  };
  
  const renderMessageContent = (content: string) => {
    const codeBlockRegex = /```([\w-]*)\n([\s\S]*?)```/g;
    
    let parts = [];
    let lastIndex = 0;
    let match;
    
    while ((match = codeBlockRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: content.slice(lastIndex, match.index)
        });
      }
      
      const language = match[1].trim() || 'text';
      const code = match[2].trim();
      parts.push({
        type: 'code',
        language,
        content: code
      });
      
      lastIndex = match.index + match[0].length;
    }
    
    if (lastIndex < content.length) {
      parts.push({
        type: 'text',
        content: content.slice(lastIndex)
      });
    }
    
    if (parts.length === 0) {
      return <p className="whitespace-pre-wrap">{content}</p>;
    }
    
    return (
      <div>
        {parts.map((part, index) => {
          if (part.type === 'code') {
            return (
              <div key={index} className="my-2 rounded-md overflow-hidden">
                <SyntaxHighlighter 
                  language={part.language} 
                  style={tomorrow}
                  customStyle={{ margin: 0 }}
                  wrapLines={true}
                  wrapLongLines={true}
                >
                  {part.content}
                </SyntaxHighlighter>
              </div>
            );
          } else {
            return <p key={index} className="whitespace-pre-wrap mb-2">{part.content}</p>;
          }
        })}
      </div>
    );
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button 
        onClick={togglePanel}
        className="fixed bottom-6 right-6 z-20 bg-primary-600 text-white p-3 rounded-full shadow-lg hover:bg-primary-700 transition-colors"
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {isOpen ? <FiX size={20} /> : <FiMessageSquare size={20} />}
      </button>

      {/* Resize Handle */}
      {isOpen && (
        <div
          ref={resizeRef}
          className="fixed z-20 w-1 h-full bg-primary-200 hover:bg-primary-400 cursor-col-resize"
          style={{ 
            left: `calc(100% - ${panelWidth}px - 1px)`,
            top: 0
          }}
          onMouseDown={startResizing}
        />
      )}

      {/* Chat Panel */}
      <div 
        className="fixed right-0 top-0 h-full bg-white shadow-lg z-10 transition-all duration-300 ease-in-out overflow-hidden flex flex-col"
        style={{ 
          width: isOpen ? `${panelWidth}px` : '0',
        }}
      >
        <div className="p-4 border-b border-neutral-200 bg-primary-50 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-primary-700">Paper Chat</h2>
          <button 
            onClick={togglePanel}
            className="text-neutral-500 hover:text-neutral-700"
            aria-label="Close chat"
          >
            <FiX size={20} />
          </button>
        </div>

        {/* Chat Messages */}
        <div className="flex-grow overflow-y-auto p-4 bg-neutral-50">
          {chatHistory.length === 0 ? (
            <div className="text-center text-neutral-500 mt-8">
              <p>No messages yet. Ask a question about the paper!</p>
            </div>
          ) : (
            chatHistory.map((chat, index) => (
              <div key={index} className="mb-4">
                {/* User message */}
                <div className="flex justify-end mb-2">
                  <div className="bg-primary-100 text-primary-800 p-3 rounded-lg max-w-[80%] break-words">
                    {chat.query}
                  </div>
                </div>
                
                {/* AI response */}
                <div className="flex justify-start">
                  <div className="bg-white border border-neutral-200 p-3 rounded-lg shadow-sm max-w-[80%] break-words">
                    {renderMessageContent(chat.response)}
                  </div>
                </div>
              </div>
            ))
          )}
          {/* Loading animation */}
          {isLoading && (
            <div className="flex justify-start my-4">
              <div className="bg-white border border-neutral-200 p-3 rounded-lg shadow-sm break-words">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '600ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Message Input */}
        <div className="p-4 border-t border-neutral-200 bg-white">
          <div className="flex items-center">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about the paper..."
              className="flex-grow p-2 border border-neutral-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              rows={2}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !message.trim()}
              className={`p-3 rounded-r-md ${
                isLoading || !message.trim()
                  ? 'bg-neutral-300 text-neutral-500'
                  : 'bg-primary-600 text-white hover:bg-primary-700'
              } transition-colors`}
              aria-label="Send message"
            >
              <FiSend size={18} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatPanel;
