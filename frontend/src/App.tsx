import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Bot, User, Download } from 'lucide-react';
import customLogo from './assets/ReCircle Logo Identity_RGB-05.png';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [showForm, setShowForm] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    organization: ''
  });
  const [formErrors, setFormErrors] = useState({
    name: '',
    email: '',
    phone: '',
    organization: ''
  });
  const [isFormSubmitted, setIsFormSubmitted] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionInitialized, setSessionInitialized] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [showWelcomePopup, setShowWelcomePopup] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastBotMessageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setShowWelcomePopup(false);
    }
  }, [isOpen]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Create a consistent fetch function with proper credentials and error handling
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    // Use API URL from environment variable, fallback to empty string for relative paths
    const baseUrl = import.meta.env.VITE_API_URL || '';
    const defaultOptions: RequestInit = {
      credentials: 'include', // This is crucial for session cookies
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    console.log(`🔗 Making API call to: ${baseUrl}${endpoint}`, defaultOptions);
    
    try {
      const response = await fetch(`${baseUrl}${endpoint}`, defaultOptions);
      console.log(`📡 Response status: ${response.status}`);
      console.log(`📡 Response headers:`, Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      const responseData = await response.json();
      console.log(`📥 Response data:`, responseData);
      return responseData;
    } catch (error) {
      console.error(`❌ API call failed for ${endpoint}:`, error);
      throw error;
    }
  };

  useEffect(() => {
    const initializeSession = async () => {
      if (sessionInitialized) return; // Prevent multiple initialization attempts
      
      setIsConnecting(true);
      try {
        console.log('🔄 Initializing session...');
        
        const sessionData = await apiCall('/session', {
          method: 'POST',
        });

        console.log('✅ Session initialized:', sessionData);
        
        // Save session_id in localStorage for debugging purposes
        localStorage.setItem("session_id", sessionData.session_id);
        setSessionInitialized(true);

        if (sessionData.user_data_collected && sessionData.user_data) {
          console.log('👋 Welcome back!', sessionData.user_data);

          setFormData({
            name: sessionData.user_data.user_name || '',
            email: sessionData.user_data.email || '',
            phone: sessionData.user_data.phone || '',
            organization: sessionData.user_data.organization || '',
          });

          setShowForm(false);
          setIsFormSubmitted(true);

          // Load chat history if available
          const loadedMessages: Message[] = [];
          if (sessionData.chat_history && sessionData.chat_history.length > 0) {
            console.log(`📜 Loading ${sessionData.chat_history.length} previous messages`);
            sessionData.chat_history.forEach((msg: any, index: number) => {
              loadedMessages.push({
                id: `history-${index}`,
                text: msg.text,
                sender: msg.role === 'user' ? 'user' : 'bot',
                timestamp: new Date()
              });
            });
          }

          const welcomeMessage: Message = {
            id: Date.now().toString(),
            text: `🌟 Welcome back, ${sessionData.user_data.user_name?.split(' ')[0] || 'there'}!\nHow can I help you today?`,
            sender: 'bot',
            timestamp: new Date()
          };
          setMessages([...loadedMessages, welcomeMessage]);
        } else {
          console.log('📝 New session, please fill out the form.');
          setShowForm(true);
          setIsFormSubmitted(false);
        }
      } catch (error) {
        console.error("❌ Session initialization failed:", error);
        setSessionInitialized(false);
        
        // Show an error message to the user
        const errorMessage: Message = {
          id: Date.now().toString(),
          text: "⚠️ There was an issue connecting to the server. Please try refreshing the page.",
          sender: 'bot',
          timestamp: new Date()
        };
        setMessages([errorMessage]);
      } finally {
        setIsConnecting(false);
      }
    };

    initializeSession();
  }, []); // Empty dependency array ensures this runs only once on mount

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Refactored function to handle sending any query to the backend
  const submitQuery = async (queryText: string) => {
    if (!queryText.trim() || !isFormSubmitted || !sessionInitialized) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: queryText,
      sender: 'user',
      timestamp: new Date()
    };

    // Prepare history for the API call (all messages *before* the new one)
    const historyForApi = messages.map(msg => ({
      role: msg.sender === 'user' ? 'user' : 'bot',
      text: msg.text,
    }));

    setIsTyping(true);
    setMessages(prev => [...prev, userMessage]);

    try {
      const data = await apiCall('/query', {
        method: 'POST',
        body: JSON.stringify({
          text: queryText,
          history: historyForApi, // Send history
        }),
      });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.answer || "Sorry, I couldn't process your request.",
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
      
      // Handle connection suggestions based on intent
      if (data.intent?.should_connect) {
        console.log('🔥 High interest detected:', data.intent);
        // You can add special UI indicators here for high-interest users
      }

      // Update suggested questions dynamically from backend response
      if (data.similar_questions && Array.isArray(data.similar_questions)) {
        setSuggestedQuestions(data.similar_questions);
      }
      
      setTimeout(() => {
        lastBotMessageRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (error) {
      console.error('❌ Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I'm having trouble connecting. Please try again later.",
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setSuggestedQuestions([]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSendMessage = async () => {
    const currentMessage = message.trim();
    if (currentMessage) {
      setMessage('');
      await submitQuery(currentMessage);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Validation functions
  const isValidEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email.trim());
  };

  const isValidPhone = (phone: string) => {
    const cleanPhone = phone.replace(/\D/g, '');
    return cleanPhone.length === 10 || (cleanPhone.length === 12 && cleanPhone.startsWith('91'));
  };

  const isValidName = (name: string) => {
    const nameRegex = /^[a-zA-Z]+(?:\s[a-zA-Z]+)*$/;
    const cleanName = name.trim().replace(/\s+/g, ' ');
    return cleanName.length > 0 && nameRegex.test(cleanName);
  };

  const validateField = (field: string, value: string) => {
    let error = '';
    switch (field) {
      case 'name':
        if (!isValidName(value)) {
          error = 'Please enter a valid name (letters and spaces only).';
        }
        break;
      case 'email':
        if (!isValidEmail(value)) {
          error = 'Oops! Your email address looks incomplete. Please check again.';
        }
        break;
      case 'phone':
        if (!isValidPhone(value)) {
          error = 'Please enter a valid 10-digit phone number.';
        }
        break;
      case 'organization':
        if (value.trim().length === 0 || value.length > 100) {
          error = 'Please enter a valid organization name (max 100 characters).';
        }
        break;
    }
    setFormErrors(prev => ({ ...prev, [field]: error }));
  };

  const handleFormChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    validateField(field, value);
  };

  const isFormValid = () => {
    return isValidName(formData.name) &&
           isValidEmail(formData.email) &&
           isValidPhone(formData.phone) &&
           formData.organization.trim().length > 0 &&
           Object.values(formErrors).every(error => error === '');
  };

  const handleFormSubmit = async () => {
    if (isFormValid() && sessionInitialized) {
      try {
        console.log('📤 Submitting user data...');
        
        const userData = {
          name: formData.name.trim().replace(/\s+/g, ' '),
          email: formData.email.trim().toLowerCase(),
          phone: formData.phone.replace(/\D/g, ''),
          organization: formData.organization.trim()
        };

        console.log('📋 User data being sent:', userData);

        const data = await apiCall('/collect_user_data', {
          method: 'POST',
          body: JSON.stringify(userData),
        });

        console.log("✅ User data submitted successfully:", data);
        
        // On successful submission, hide form and show welcome message
        setShowForm(false);
        setIsFormSubmitted(true);
        
        // Load chat history if available (for returning users)
        const loadedMessages: Message[] = [];
        if (data.chat_history && data.chat_history.length > 0) {
          console.log(`📜 Loading ${data.chat_history.length} previous messages`);
          data.chat_history.forEach((msg: any, index: number) => {
            loadedMessages.push({
              id: `history-${index}`,
              text: msg.text,
              sender: msg.role === 'user' ? 'user' : 'bot',
              timestamp: new Date()
            });
          });
        }
        
        const welcomeMessage: Message = {
          id: Date.now().toString(),
          text: `🌟 Great to meet you, ${formData.name.split(' ')[0]}!\nWhat would you like to know today?`,
          sender: 'bot',
          timestamp: new Date()
        };
        setMessages([...loadedMessages, welcomeMessage]);
        setSuggestedQuestions([]);
        
      } catch (err) {
        console.error("❌ Failed to submit user data:", err);
        
        // Show an error to the user in the chat
        const errorMessage: Message = {
          id: Date.now().toString(),
          text: `Sorry, there was an error submitting your information: ${err instanceof Error ? err.message : 'Unknown error'}`,
          sender: 'bot',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } else if (!sessionInitialized) {
      console.error("❌ Session not initialized");
      const errorMessage: Message = {
        id: Date.now().toString(),
        text: "Session not ready. Please refresh the page and try again.",
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleSuggestionClick = async (question: string) => {
    // Check if this is the contact button
    const isContactButton = question.toLowerCase().includes('connect me to recircle');
    
    if (isContactButton) {
      // Add user message first
      const userMessage: Message = {
        id: Date.now().toString(),
        text: question,
        sender: 'user',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      setIsTyping(true);
      
      // Trigger immediate backend notification
      try {
        const response = await apiCall('/trigger_contact_intent', {
          method: 'POST',
        });
        console.log('✅ Contact button clicked - backend notified immediately');
        
        // Show the response message to user immediately
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: response.message,
          sender: 'bot',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botMessage]);
        
        // Keep existing suggestions visible for continued conversation
        // Backend will provide new dynamic suggestions on next query
        
        setIsTyping(false);
        return; // Don't submit as regular query
      } catch (error) {
        console.error('❌ Failed to trigger contact intent:', error);
        setIsTyping(false);
      }
    }
    
    // Continue with normal query submission for other suggestions
    await submitQuery(question);
  };

  const handleDownloadChat = async () => {
    console.log('📥 Download button clicked!');
    try {
      const sessionId = localStorage.getItem('session_id');
      console.log('Session ID:', sessionId);
      if (!sessionId) {
        alert('No session found. Please start a conversation first.');
        return;
      }
      
      console.log('Fetching PDF from:', `/download_chat/${sessionId}`);
      const response = await fetch(`/download_chat/${sessionId}`, {
        credentials: 'include'
      });
      
      console.log('Response status:', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error('Failed to download chat');
      }
      
      const blob = await response.blob();
      console.log('Blob size:', blob.size);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const firstName = formData.name.split(' ')[0];
      a.download = `${firstName}'s_Discussion_with_ReBot.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      console.log('✅ Download complete!');
    } catch (error) {
      console.error('❌ Error downloading chat:', error);
      alert('Failed to download chat. Please try again.');
    }
  };

  return (
    <div className="bg-transparent relative" style={{ pointerEvents: 'none' }}>
      <style>{`
        @keyframes pulse-glow {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
            box-shadow: 0 0 20px 5px rgba(1, 41, 138, 0.8), 0 0 40px 10px rgba(1, 41, 138, 0.4);
          }
          50% {
            opacity: 0.7;
            transform: scale(1.15);
            box-shadow: 0 0 40px 15px rgba(1, 41, 138, 0.4), 0 0 60px 20px rgba(1, 41, 138, 0.2);
          }
        }
        .pulse-animation {
          animation: pulse-glow 1.5s ease-in-out infinite;
        }
      `}</style>
      {/* Welcome Popup */}
      {showWelcomePopup && !isOpen && (
        <div className="fixed bottom-24 right-5 z-40 animate-in slide-in-from-right-5 duration-500" style={{ pointerEvents: 'auto' }}>
          <div className="rounded-xl shadow-2xl p-3 relative" style={{
            maxWidth: '240px',
            background: 'linear-gradient(135deg, #01298a 0%, #0147d4 100%)',
            boxShadow: '0 10px 40px rgba(1, 41, 138, 0.3)'
          }}>
            <button
              onClick={() => setShowWelcomePopup(false)}
              className="absolute top-1 right-1 text-white hover:text-gray-200 w-5 h-5 flex items-center justify-center rounded-full hover:bg-white/20 transition-all text-sm"
            >
              ✕
            </button>
            <div className="pr-4">
              <p className="text-white font-bold text-sm mb-1">👋 Hi there!</p>
              <p className="text-white/90 text-xs leading-snug">Need help with EPR? ReCircle is here to help you!</p>
            </div>
          </div>
        </div>
      )}

      {/* Chat Widget */}
      <div className="fixed bottom-5 right-5 z-50" style={{ pointerEvents: 'auto' }}>
        {/* Chat Button */}
        {!isOpen && (
          <button
            onClick={() => setIsOpen(true)}
            className="w-15 h-15 rounded-lg shadow-2xl hover:shadow-blue-500/25 transition-all duration-300 hover:scale-110 flex items-center justify-center pulse-animation"
            style={{ width: '60px', height: '60px', backgroundColor: '#01298a' }}
          >
            <img src={customLogo} alt="Chat Bot Logo" className="w-15 h-10 object-contain" />
          </button>
        )}

        {/* Chat Window */}
        {isOpen && (
          <div className="w-85 h-96 bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-300"
               style={{ width: '340px', height: '500px' }}>
            {/* Header */}
            <div className="p-3 flex items-center justify-between"
                 style={{ backgroundColor: '#01298a', color: 'white' }}>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-13 h-13 rounded-full flex items-center justify-center">
                    <img src={customLogo} alt="Chat Bot Logo" className="w-10 h-10 object-contain" />
                  </div>
                  <div className={`absolute bottom-0 right-0 w-4 h-4 rounded-full border-2 border-blue-900 ${
                    sessionInitialized ? 'bg-green-500' : isConnecting ? 'bg-yellow-500' : 'bg-red-500'
                  }`}></div>
                </div>
                <div>
                  <h3 className="text-white font-bold text-base">ReBot</h3>
                  <p className="text-xs text-gray-200">
                    {sessionInitialized ? 'Online' : isConnecting ? 'Connecting...' : 'Offline'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {isFormSubmitted && messages.some(m => m.sender === 'user') && (
                  <button
                    onClick={handleDownloadChat}
                    className="text-white hover:opacity-70 transition-opacity duration-200"
                    title="Download chat transcript"
                  >
                    <Download className="w-5 h-5" />
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-white hover:opacity-70 transition-opacity duration-200 text-lg font-bold"
                >
                  ✖
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-3"
                 style={{
                   backgroundColor: '#f7f1ee',
                   backgroundImage: `url('data:image/svg+xml,%3Csvg width=%2260%22 height=%2260%22 viewBox=%220 0 60 60%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cg fill=%22none%22 fill-rule=%22evenodd%22%3E%3Cg fill=%22%23E5E5E5%22 fill-opacity=%220.1%22%3E%3Ccircle cx=%227%22 cy=%227%22 r=%227%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')`,
                   backgroundSize: '120px',
                   backgroundRepeat: 'repeat'
                 }}>
              
              {/* Connection Status */}
              {isConnecting && (
                <div className="flex justify-center items-center h-32">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-900 mx-auto mb-2"></div>
                    <p className="text-sm text-gray-600">Connecting to server...</p>
                  </div>
                </div>
              )}

              {/* Connection Error */}
              {!sessionInitialized && !isConnecting && messages.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                  <div className="flex items-center">
                    <div className="text-red-500 text-sm">
                      ⚠️ Connection issue detected. Please refresh the page to try again.
                    </div>
                  </div>
                </div>
              )}
              
              {/* Form */}
              {showForm && sessionInitialized && (
                <div className="flex justify-center mb-4">
                  <div className="border border-gray-300 rounded-lg p-5 shadow-lg max-w-xs w-full" style={{ backgroundColor: '#ffffff' }}>
                    <h3 className="text-center text-lg font-semibold mb-3" style={{ color: '#01298a' }}>Let's get to know you!</h3>
                    <form className="space-y-4">
                      <div>
                        <label className="block text-sm text-gray-700 mb-1">Name</label>
                        <input
                          type="text"
                          placeholder="Enter your full name"
                          value={formData.name}
                          onChange={(e) => handleFormChange('name', e.target.value)}
                          onBlur={() => validateField('name', formData.name)}
                          className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-600"
                        />
                        {formErrors.name && <div className="text-red-500 text-xs mt-1">{formErrors.name}</div>}
                      </div>
                      
                      <div>
                        <label className="block text-sm text-gray-700 mb-1">Email</label>
                        <input
                          type="email"
                          placeholder="Enter your email address"
                          value={formData.email}
                          onChange={(e) => handleFormChange('email', e.target.value)}
                          onBlur={() => validateField('email', formData.email)}
                          className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-600"
                        />
                        {formErrors.email && <div className="text-red-500 text-xs mt-1">{formErrors.email}</div>}
                      </div>
                      
                      <div>
                        <label className="block text-sm text-gray-700 mb-1">Phone</label>
                        <input
                          type="text"
                          placeholder="Enter your phone number"
                          value={formData.phone}
                          onChange={(e) => {
                            const value = e.target.value.replace(/\D/g, '');
                            if (value.length <= 10) {
                              handleFormChange('phone', value);
                            }
                          }}
                          onBlur={() => validateField('phone', formData.phone)}
                          maxLength={10}
                          className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-600"
                        />
                        {formErrors.phone && <div className="text-red-500 text-xs mt-1">{formErrors.phone}</div>}
                      </div>
                      
                      <div>
                        <label className="block text-sm text-gray-700 mb-1">Organization</label>
                        <input
                          type="text"
                          placeholder="Enter your organization name"
                          value={formData.organization}
                          onChange={(e) => handleFormChange('organization', e.target.value)}
                          onBlur={() => validateField('organization', formData.organization)}
                          className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-600"
                        />
                        {formErrors.organization && <div className="text-red-500 text-xs mt-1">{formErrors.organization}</div>}
                      </div>
                      
                      <button
                        type="button"
                        onClick={handleFormSubmit}
                        disabled={!isFormValid() || !sessionInitialized}
                        className="w-full py-2 px-4 text-white rounded text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        style={{ backgroundColor: '#01298a' }}
                      >
                        {sessionInitialized ? 'Submit' : 'Connecting...'}
                      </button>
                    </form>
                  </div>
                </div>
              )}

              {/* Messages */}
              {messages.map((msg, index) => {
                // Convert markdown formatting, URLs and emails to HTML
                const renderMessageWithFormatting = (text: string) => {
                  // First, split by newlines to preserve line breaks
                  const lines = text.split('\n');

                  return lines.map((line, lineIndex) => {
                    // Process each line for markdown and links
                    let processedLine: React.ReactNode[] = [];

                    // Check if it's a bullet point
                    const bulletMatch = line.match(/^(\s*[-*]\s+)(.*)/);
                    if (bulletMatch) {
                      const bulletContent = bulletMatch[2];
                      processedLine = [
                        <span key={`bullet-${lineIndex}`}>• </span>,
                        ...processMarkdownAndLinks(bulletContent)
                      ];
                    } else {
                      processedLine = processMarkdownAndLinks(line);
                    }

                    return (
                      <React.Fragment key={lineIndex}>
                        {processedLine}
                        {lineIndex < lines.length - 1 && <br />}
                      </React.Fragment>
                    );
                  });
                };

                const processMarkdownAndLinks = (text: string): React.ReactNode[] => {
                  // Regex patterns for markdown and links
                  const combinedRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|https?:\/\/[^\s]+|[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/g;

                  const parts = text.split(combinedRegex);

                  return parts.map((part, i) => {
                    // Bold: **text**
                    if (part.startsWith('**') && part.endsWith('**')) {
                      return <strong key={i}>{part.slice(2, -2)}</strong>;
                    }
                    // Italic: *text* (but not at word boundaries)
                    else if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
                      return <em key={i}>{part.slice(1, -1)}</em>;
                    }
                    // URLs
                    else if (part.startsWith('http://') || part.startsWith('https://')) {
                      return <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{part}</a>;
                    }
                    // Emails
                    else if (part.includes('@') && part.includes('.')) {
                      const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+$/;
                      if (emailRegex.test(part)) {
                        return <a key={i} href={`mailto:${part}`} className="text-blue-600 hover:underline">{part}</a>;
                      }
                    }
                    return <span key={i}>{part}</span>;
                  });
                };
                
                return (
                  <div 
                    key={msg.id} 
                    ref={msg.sender === 'bot' && index === messages.length - 1 ? lastBotMessageRef : null}
                    className={`flex mb-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`flex items-end gap-2 max-w-xs ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                      <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#01298a' }}>
                        {msg.sender === 'user' ? (
                          <User className="w-5 h-5 text-white" />
                        ) : (
                          <Bot className="w-5 h-5 text-white" />
                        )}
                      </div>
                      <div className={`px-4 py-3 rounded-2xl shadow-sm ${
                        msg.sender === 'user'
                          ? 'bg-purple-100 text-gray-800'
                          : 'bg-white text-gray-800'
                      }`}>
                        <div className="text-sm leading-relaxed">{renderMessageWithFormatting(msg.text)}</div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Typing Indicator */}
              {isTyping && (
                <div className="flex mb-3 justify-start">
                  <div className="flex items-end gap-2 max-w-xs flex-row">
                    <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#01298a' }}>
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="px-4 py-3 rounded-2xl shadow-sm bg-white text-gray-800">
                      <div className="flex items-center justify-center space-x-1 h-5">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Suggested Questions */}
              {isFormSubmitted && messages.length > 0 && suggestedQuestions.length > 0 && (
                <div className="mt-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">Would you also like to know about?</div>
                  <div className="space-y-2">
                    {suggestedQuestions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(question)}
                        className="block w-full text-left px-3 py-2 text-sm rounded-full transition-colors duration-200"
                        style={{ color: '#01298a', borderWidth: '2px', borderColor: '#01298a' }}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Removed fallback - suggestions always show now */}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 bg-white border-t border-gray-100">
              <div className="relative">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask your question..."
                  maxLength={250}
                  disabled={!isFormSubmitted || !sessionInitialized}
                  className="w-full px-4 py-3 pr-12 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!message.trim() || !isFormSubmitted || !sessionInitialized}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 w-8 h-8 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" style={{ color: message.trim() && isFormSubmitted && sessionInitialized ? '#01298a' : '#9CA3AF' }} />
                </button>
              </div>
              <div className="text-xs text-gray-500 mt-1 ml-4">
                The ReBot may make mistakes. For more information, please visit the CPCB portal.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
