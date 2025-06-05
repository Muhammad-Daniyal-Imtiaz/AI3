'use client';
import { useState, useRef, useEffect } from 'react';
import { SendHorizonal, Loader2 } from 'lucide-react';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      content: input,
      role: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input })
      });

      if (!response.ok) throw new Error('API error');
      const data = await response.json();

      const botMessage = {
        id: Date.now().toString(),
        content: data.response,
        role: 'assistant',
        sources: data.sources
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: "Error processing your request",
        role: 'assistant'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-purple-900 to-indigo-900">
      {/* Left Side: Chat History */}
      <div className="w-1/4 border-r border-purple-700 p-4 overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4 text-purple-300">Chat History</h2>
        <ul className="space-y-2">
          {messages.map((msg) => (
            <li
              key={msg.id}
              className="p-3 rounded-lg bg-purple-900 cursor-pointer hover:bg-purple-800 transition-colors"
              onClick={scrollToBottom}
            >
              <span className="text-purple-300 font-bold">
                {msg.role === 'user' ? 'You' : 'Assistant'}:
              </span>
              <span className="text-white ml-2">
                {msg.content.slice(0, 30)}...
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Right Side: Chat Interface */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-purple-900 p-4 border-b border-purple-700 shadow-lg">
          <h1 className="text-3xl font-bold text-purple-300">Document Chat</h1>
          <p className="text-purple-200">Ask questions about your documents</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-3/4 ${
                msg.role === 'user' ? 'ml-auto' : 'mr-auto'
              }`}
            >
              <div
                className={`p-4 rounded-lg shadow-lg ${
                  msg.role === 'user'
                    ? 'bg-purple-500 text-white'
                    : 'bg-indigo-900 text-white'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-purple-700">
                    <p className="text-sm text-purple-300">Sources:</p>
                    {msg.sources.map((source, index) => (
                      <div key={index} className="text-sm text-purple-200 mt-1">
                        <p>Score: {source.score.toFixed(2)}</p>
                        <p className="text-xs">{source.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="mr-auto">
              <div className="p-4 bg-indigo-900 rounded-lg shadow-lg">
                <div className="flex gap-2">
                  <Loader2 className="animate-spin" />
                  <Loader2 className="animate-spin" />
                  <Loader2 className="animate-spin" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form
          onSubmit={handleSubmit}
          className="p-4 border-t border-purple-700 bg-purple-900"
        >
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your documents..."
              className="flex-1 p-3 rounded-lg bg-purple-800 text-white placeholder-purple-300 border border-purple-600 focus:outline-none focus:border-purple-400"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="p-3 bg-purple-500 text-white rounded-lg shadow-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="animate-spin" />
              ) : (
                <SendHorizonal />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}