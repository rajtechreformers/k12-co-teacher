"use client";

import { useAuth } from "react-oidc-context";
import { motion } from "framer-motion";
import { useParams, useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import useRequireAuth from "../../../../../components/useRequireAuth";
import { Card, CardHeader, CardTitle, CardContent } from "../../../../../components/ui/card";
import { Button } from "../../../../../components/ui/button";
import { Badge } from "../../../../../components/ui/badge";
import { 
  ArrowLeft, 
  Send, 
  Users, 
  MessageSquare,
  BookOpen,
  User,
  Bot,
  MoreVertical,
  Plus
} from "lucide-react";

import { ChatMessage, ChatHistory } from "../../../../../types/chat";
import { getStudentsByClassId, getClassesForDashboard, getChatHistory, getChatMessages } from "../../../../../lib/api";
import { studentCache } from "../../../../../lib/studentCache";
import { useWebSocket } from "../../../../../hooks/useWebSocket";
import ReactMarkdown from "react-markdown";

export default function StudentChatPage() {
  const auth = useAuth();
  const params = useParams();
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [classInfo, setClassInfo] = useState<{title: string, section: string, color: string} | null>(null);
  const [students, setStudents] = useState<Record<string, string>>({});
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentAIMessage, setCurrentAIMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useRequireAuth();

  // Clear cache on sign out
  useEffect(() => {
    if (!auth.isAuthenticated && !auth.isLoading) {
      studentCache.clear();
    }
  }, [auth.isAuthenticated, auth.isLoading]);

  const classId = params.classId as string;
  const studentId = params.studentId as string;

  const { isConnected, connect, disconnect, sendMessage } = useWebSocket({
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
    onMessage: (data) => {
      if (data.message) {
        setCurrentAIMessage(prev => prev + data.message);
      }
      
      // If we receive a sessionId from the server, update our sessionId
      if ('sessionId' in data && data.sessionId && !sessionId) {
        console.log('Received sessionId from server (student chat):', data.sessionId);
        if (typeof data.sessionId === 'string') {
          setSessionId(data.sessionId);
        }
      }
    },
    onError: (error) => {
      const errorDetails = {
        type: error.type || 'error',
        url: process.env.NEXT_PUBLIC_WS_URL,
        message: error instanceof ErrorEvent ? error.message : 'WebSocket connection failed',
        timestamp: new Date().toISOString(),
        classId,
        studentId
      };
      console.error('WebSocket error in StudentChatPage:', errorDetails);
    },
    onClose: (event) => {
      console.log('WebSocket disconnected:', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
        timestamp: new Date().toISOString()
      });
    }
  });

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const fetchData = async () => {
      if (!studentId || !classId || !auth.user?.profile?.email) return;
      
      try {
        setLoading(true);
        
        // Get class info from the classes API
        const allClasses = await getClassesForDashboard(auth.user.profile.email);
        const currentClass = allClasses.find(cls => cls.classID === classId);
        
        if (currentClass) {
          setClassInfo({
            title: currentClass.classTitle,
            section: currentClass.sectionNumber,
            color: "from-purple-500 to-pink-600"
          });
        }
        
        // Check cache first
        const cachedStudents = studentCache.get(classId);
        if (cachedStudents) {
          setStudents(cachedStudents);
        } else {
          // Fetch and cache students for THIS specific class only
          const classStudents = await getStudentsByClassId(classId);
          studentCache.set(classId, classStudents);
          setStudents(classStudents);
        }
        
        // Fetch chat history for this teacher and class
        if (auth.user?.profile?.email) {
          try {
            const history = await getChatHistory(auth.user.profile.email, classId);
            
            // Transform the data to match our ChatHistory interface
            // Sort history by created_at timestamp (newest first for chat history)
            const sortedHistory = [...history].sort((a, b) => b.created_at - a.created_at);
            
            const formattedHistory: ChatHistory[] = sortedHistory.map(item => {
              // Extract conversation_id from sortId (format: CONV#uuid)
              const conversationId = item.sortId.split('#')[1];
              
              // Use the type from the API response if available, otherwise infer it
              const chatType: 'general' | 'student' = (item.type === 'student' || item.type === 'general') ? item.type : 'general';
              
              // For student chats, get the student ID from the student_ids array
              const studentIdFromItem = chatType === 'student' && item.student_ids && item.student_ids.length === 1 
                ? item.student_ids[0] 
                : null;
              
              return {
                id: parseInt(item.created_at.toString()),
                title: item.title || (chatType === 'student' ? `${studentIdFromItem ? students[studentIdFromItem] : 'Student'} Chat` : 'General Chat'),
                lastMessage: '', // We don't have this in the response
                time: formatTimestamp(new Date(item.created_at * 1000)),
                type: chatType,
                studentId: studentIdFromItem ? parseInt(studentIdFromItem) : undefined,
                conversationId
              };
            });
            
            setChatHistory(formattedHistory);
            
            // Find existing student chat for this student
            const existingChat = formattedHistory.find(chat => 
              chat.type === 'student' && chat.studentId === parseInt(studentId)
            );
            
            // Load messages if found, otherwise leave it null for a new chat
            if (existingChat) {
              // Load messages for this conversation
              try {
                // Clear current state first
                setMessages([]);
                setCurrentAIMessage("");
                
                const chatMessages = await getChatMessages(auth.user.profile.email!, existingChat.conversationId!);

                
                // Transform messages to match our ChatMessage interface
                // Sort messages by created_at timestamp (oldest first)
                const sortedMessages = [...chatMessages].sort((a, b) => a.created_at - b.created_at);
                
                const formattedMessages = sortedMessages.map((msg, index) => ({
                  id: index + 1,
                  sender: msg.sender === "user" ? "Teacher" : "AI Assistant",
                  message: msg.message,
                  time: formatTimestamp(new Date(msg.created_at * 1000)),
                  isTeacher: msg.sender === "user"
                }));
                
                // Set session ID after loading messages to avoid WebSocket issues
                setTimeout(() => {
                  setSessionId(existingChat.conversationId!);
                  setMessages(formattedMessages);
                }, 0);
              } catch (error) {
                console.error('Failed to fetch chat messages:', error);
              }
            }
          } catch (error) {
            console.error('Failed to fetch chat history:', error);
          }
        }
        
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (auth.isAuthenticated && !auth.isLoading) {
      fetchData();
    }
  }, [studentId, classId, auth.isAuthenticated, auth.isLoading, auth.user?.profile?.email]);

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const handleSendMessage = () => {
    if (message.trim() && isConnected) {
      const now = new Date();
      
      // If there's a current AI message, add it to the messages array first
      if (currentAIMessage) {
        const aiMessage = {
          id: messages.length + 1,
          sender: "AI Assistant",
          message: currentAIMessage,
          time: formatTimestamp(now),
          isTeacher: false
        };
        setMessages(prev => [...prev, aiMessage]);
      }
      
      // Then add the user's message
      const newMessage = {
        id: messages.length + (currentAIMessage ? 2 : 1),
        sender: "Teacher",
        message: message.trim(),
        time: formatTimestamp(now),
        isTeacher: true
      };
      setMessages(prev => [...prev, newMessage]);
      
      // Debug log to verify the session ID before sending
      console.log('Current sessionId before sending message (student chat):', sessionId);
      
      // Send to WebSocket with single student ID
      const payload = {
        message: message.trim(),
        studentIDs: [studentId],
        sessionId: sessionId,  // Changed from conversation_id to sessionId
        teacherId: auth.user?.profile?.email,
        classId: classId
      };
      
      // Debug log to verify the payload
      console.log('Sending payload with sessionId (student chat):', payload.sessionId);
      
      sendMessage(payload);
      setMessage("");
      setCurrentAIMessage("");
    } else if (!isConnected) {
      console.warn('WebSocket not connected, cannot send message (student chat)');
    }
  };

  const handleNewChat = () => {
    // Reset session ID to start a new conversation
    setSessionId(null);
    setMessages([]);
    setCurrentAIMessage("");
  };

  const handleChatClick = async (chat: ChatHistory) => {
    if (chat.type === "general" && chat.conversationId) {
      // Navigate to general chat
      router.push(`/chat/${classId}`);
    } else if (chat.type === "student" && chat.conversationId) {
      // First set loading state to true
      setLoading(true);
      // Clear current state
      setCurrentAIMessage("");
      setMessages([]);
      // Clear session ID to avoid showing the wrong conversation as selected
      setSessionId(null);
      
      try {
        if (auth.user?.profile?.email) {
          const chatMessages = await getChatMessages(auth.user.profile.email, chat.conversationId);
          
          // Transform messages to match our ChatMessage interface
          // Sort messages by created_at timestamp (oldest first)
          const sortedMessages = [...chatMessages].sort((a, b) => a.created_at - b.created_at);
          
          const formattedMessages = sortedMessages.map((msg, index) => ({
            id: index + 1,
            sender: msg.sender === "user" ? "Teacher" : "AI Assistant",
            message: msg.message,
            time: formatTimestamp(new Date(msg.created_at * 1000)),
            isTeacher: msg.sender === "user"
          }));
          
          // Set session ID after loading messages to avoid WebSocket issues
          // Use setTimeout to ensure the UI has time to update
          setTimeout(() => {
            setSessionId(chat.conversationId!);
            setMessages(formattedMessages);
          }, 0);
        }
      } catch (error) {
        console.error('Failed to fetch chat messages:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  if (auth.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
        />
        <p className="ml-4 text-lg font-medium text-gray-700">Loading chat...</p>
      </div>
    );
  }



  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex">
      {/* Left Sidebar - All Chats */}
      <div className="w-80 bg-white/90 backdrop-blur-xl border-r border-gray-200 flex flex-col h-screen">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <Button
              size="icon"
              onClick={() => router.push('/dashboard')}
              className="bg-gray-200 hover:bg-gray-300"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                  <h2 className="text-lg font-bold text-gray-900">Loading...</h2>
                </div>
              ) : (
                <>
                  <h2 className="text-lg font-bold text-gray-900">{classInfo?.title}</h2>
                  <p className="text-sm text-gray-600">Section {classInfo?.section}</p>
                </>
              )}
            </div>
          </div>
          <motion.div whileHover={{ scale: 1.02 }}>
            <Button 
              onClick={handleNewChat}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:shadow-lg transition-all"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Student Chat
            </Button>
          </motion.div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 max-h-[calc(100vh-180px)]">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
            <MessageSquare className="h-4 w-4 mr-2" />
            All Chat History
          </h3>
          <div className="space-y-2">
            {loading ? (
              <div className="flex justify-center items-center py-8">
                <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                <p className="ml-2 text-sm text-gray-500">Loading chats...</p>
              </div>
            ) : chatHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No chat history yet</p>
                <p className="text-xs mt-1">Start a conversation to see it here</p>
              </div>
            ) : (
              chatHistory.map((chat) => (
                <motion.div
                  key={chat.id}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => handleChatClick(chat)}
                  className={`p-3 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors ${sessionId === chat.conversationId ? 'bg-purple-50 border border-purple-200' : ''}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <h4 className="font-medium text-gray-900 text-sm truncate max-w-[70%]" title={chat.title}>{chat.title}</h4>
                    <Badge className={`text-xs ${chat.type === 'student' ? 'bg-purple-500' : 'bg-blue-500'} text-white flex-shrink-0`}>
                      {chat.type === 'student' ? 'Student' : 'General'}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-600 truncate">{chat.lastMessage || ''}</p>
                  <p className="text-xs text-gray-500 mt-1">{chat.time}</p>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-screen">
        {/* Chat Header */}
        <div className="bg-white/90 backdrop-blur-xl border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
                <User className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Chat for {students[studentId] || 'Student'}</h1>
                <p className="text-xs text-gray-500">Student ID: {studentId}</p>
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                    <p className="text-sm text-gray-600">Loading class info...</p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">{classInfo?.title} - Section {classInfo?.section}</p>
                )}
              </div>
            </div>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Messages Area - Fixed height container */}
        <div className="flex-1 overflow-hidden flex flex-col max-h-[calc(100vh-180px)]">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="flex justify-center items-center h-full">
                <p className="text-gray-400 text-lg">Welcome to a new chat, feel free to ask for tips on improving the lesson plan for the day!</p>
              </div>
            )}
            {messages.map((msg, index) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className={`flex ${msg.isTeacher ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-start space-x-3 ${
                  msg.isTeacher 
                    ? 'max-w-xs lg:max-w-md flex-row-reverse space-x-reverse' 
                    : 'max-w-2xl lg:max-w-4xl w-full'
                }`}>
                  <div className={`p-2 rounded-full flex-shrink-0 ${msg.isTeacher ? 'bg-gradient-to-br from-blue-500 to-purple-600' : 'bg-gray-300'}`}>
                    {msg.isTeacher ? <User className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-gray-600" />}
                  </div>
                  <div className={`rounded-2xl p-4 ${
                    msg.isTeacher 
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white' 
                      : 'bg-white shadow-md text-black border border-gray-200'
                  }`}>
                    {!msg.isTeacher && <p className="text-sm font-medium mb-2 text-gray-700">{msg.sender}</p>}
                    {msg.isTeacher ? (
                      <p className="text-sm">{msg.message}</p>
                    ) : (
                      <div className="text-sm prose prose-sm max-w-none prose-gray">
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                            ul: ({ children }) => <ul className="mb-2 last:mb-0 ml-4 list-disc">{children}</ul>,
                            ol: ({ children }) => <ol className="mb-2 last:mb-0 ml-4 list-decimal">{children}</ol>,
                            li: ({ children }) => <li className="mb-1">{children}</li>,
                            code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">{children}</code>,
                            pre: ({ children }) => <pre className="bg-gray-100 p-2 rounded-lg overflow-x-auto text-xs">{children}</pre>,
                            h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-base font-semibold mb-2">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-sm font-medium mb-1">{children}</h3>,
                          }}
                        >
                          {msg.message}
                        </ReactMarkdown>
                      </div>
                    )}
                    <p className={`text-xs mt-2 ${msg.isTeacher ? 'text-blue-100' : 'text-gray-500'}`}>{msg.time}</p>
                  </div>
                </div>
              </motion.div>
            ))}
            {currentAIMessage && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="flex items-start space-x-3 max-w-2xl lg:max-w-4xl w-full">
                  <div className="p-2 rounded-full bg-gray-300 flex-shrink-0">
                    <Bot className="h-4 w-4 text-gray-600" />
                  </div>
                  <div className="rounded-2xl p-4 bg-white shadow-md text-black border border-gray-200">
                    <p className="text-sm font-medium mb-2 text-gray-700">AI Assistant</p>
                    <div className="text-sm prose prose-sm max-w-none prose-gray">
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                          ul: ({ children }) => <ul className="mb-2 last:mb-0 ml-4 list-disc">{children}</ul>,
                          ol: ({ children }) => <ol className="mb-2 last:mb-0 ml-4 list-decimal">{children}</ol>,
                          li: ({ children }) => <li className="mb-1">{children}</li>,
                          code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">{children}</code>,
                          pre: ({ children }) => <pre className="bg-gray-100 p-2 rounded-lg overflow-x-auto text-xs">{children}</pre>,
                          h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-base font-semibold mb-2">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-sm font-medium mb-1">{children}</h3>,
                        }}
                      >
                        {currentAIMessage}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Message Input */}
        <div className="bg-white/90 backdrop-blur-xl border-t border-gray-200 p-4">
          <div className="flex items-center space-x-3">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your message..."
              className="flex-1 p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
            />
            <Button
              onClick={handleSendMessage}
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3 rounded-xl hover:shadow-lg transition-all"
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Student Roster */}
      <div className="w-80 bg-white/90 backdrop-blur-xl border-l border-gray-200 flex flex-col h-screen">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900 flex items-center">
            <Users className="h-5 w-5 mr-2" />
            Student Roster
          </h2>
          <p className="text-sm text-gray-600">{Object.keys(students).length} students</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 max-h-[calc(100vh-180px)]">
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(students).map(([id, name]) => (
                <motion.button
                  key={id}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => router.push(`/chat/${classId}/student/${id}`)}
                  className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors w-full text-left ${
                    id === studentId ? 'bg-purple-100 border-2 border-purple-300' : 'hover:bg-gray-100'
                  }`}
                >
                  <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full flex items-center justify-center">
                    <User className="h-5 w-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 text-sm">{name}</p>
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-gray-200">
          <motion.div whileHover={{ scale: 1.02 }}>
            <Button
              onClick={() => router.push(`/chat/${classId}`)}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              General Chat
            </Button>
          </motion.div>
        </div>
      </div>
    </div>
  );
}