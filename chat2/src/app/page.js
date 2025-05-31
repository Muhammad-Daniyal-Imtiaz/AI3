'use client';
import { useState, useRef } from 'react';
import { SendHorizonal, Loader2 } from 'lucide-react';

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

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
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input, top_k: 3 })
      });

      if (!response.ok) throw new Error('API error');
      const data = await response.json();

      const botMessage = {
        id: Date.now().toString(),
        content: data.response || "No results found",
        role: 'assistant'
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
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'linear-gradient(to bottom right, #1a002c, #2e004d)', color: '#ffffff', textAlign: 'center' }}>
      
      {/* Left Side: Chat History */}
      <div style={{ width: '25%', borderRight: '1px solid #4b0082', padding: '1rem', overflowY: 'auto', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#bb86fc' }}>Chat History</h2>
        <ul style={{ listStyleType: 'none', padding: 0 }}>
          {messages.map((msg, index) => (
            <li
              key={msg.id}
              style={{ padding: '0.75rem', borderRadius: '0.375rem', marginBottom: '0.5rem', cursor: 'pointer', transition: 'background-color 0.2s', backgroundColor: '#1a002c' }}
              onClick={() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })}
            >
              <strong style={{ color: '#bb86fc' }}>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong> {msg.content.slice(0, 30)}...
            </li>
          ))}
        </ul>
      </div>

      {/* Right Side: Chat Messages */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', textAlign: 'center' }}>
        {/* Header */}
        <div style={{ backgroundColor: '#2e004d', padding: '1rem', borderBottom: '1px solid #4b0082', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#bb86fc' }}>Document Retrieval System</h1>
          <p style={{ fontSize: '0.875rem', color: '#ffffff' }}>Ask questions about your documents</p>
        </div>

        {/* Chat Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', backgroundColor: '#2e004d', textAlign: 'center' }}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                padding: '1rem',
                borderRadius: '0.375rem',
                maxWidth: '75%',
                backgroundColor: msg.role === 'user' ? '#bb86fc' : '#4b0082',
                marginLeft: msg.role === 'user' ? 'auto' : '0',
                marginRight: msg.role === 'user' ? '0' : 'auto',
                marginBottom: '1rem',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
              }}
            >
              <div style={{ whiteSpace: 'pre-wrap', color: '#ffffff' }}>{msg.content}</div>
            </div>
          ))}
          {isLoading && (
            <div style={{ padding: '1rem', backgroundColor: '#4b0082', borderRadius: '0.375rem', marginRight: 'auto', maxWidth: '75%', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', color: '#ffffff' }}>
                <Loader2 style={{ animation: 'spin 1s linear infinite' }} />
                <Loader2 style={{ animation: 'spin 1s linear infinite 0.1s' }} />
                <Loader2 style={{ animation: 'spin 1s linear infinite 0.2s' }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} style={{ padding: '1rem', borderTop: '1px solid #4b0082', backgroundColor: '#2e004d', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your documents..."
            style={{ flex: 1, padding: '0.75rem', border: '1px solid #4b0082', borderRadius: '0.375rem', backgroundColor: '#1a002c', color: '#ffffff', outline: 'none', transition: 'border-color 0.2s' }}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            style={{ backgroundColor: '#bb86fc', color: '#000000', padding: '0.75rem 1.5rem', borderRadius: '0.375rem', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', transition: 'background-color 0.2s', opacity: isLoading || !input.trim() ? 0.5 : 1 }}
          >
            {isLoading ? <Loader2 style={{ animation: 'spin 1s linear infinite' }} /> : <SendHorizonal />}
          </button>
        </form>
      </div>
    </div>
  );
}
