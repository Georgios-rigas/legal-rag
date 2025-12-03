import { useState, useRef, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom'
import { Send, Scale, Loader2, BookOpen, AlertCircle, Copy, Check, Trash2, Eye } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import axios from 'axios'
import { Spotlight } from './components/ui/spotlight'
import { Highlight } from './components/ui/hero-highlight'
import { BackgroundGradient } from './components/ui/background-gradient'
import { motion } from 'framer-motion'
import CaseViewer from './CaseViewer'
import './App.css'

interface Source {
  case_id: number
  case_name: string
  citation: string
  decision_date: string
  court: string
  score: number
}

interface RAGResponse {
  query: string
  answer: string
  sources: Source[]
  num_sources: number
}

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
}

const API_BASE_URL = 'http://20.50.147.24'

function ChatInterface() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape to clear input
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        setInput('')
        inputRef.current?.blur()
      }
      // Ctrl/Cmd + K to focus input
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(messageId)
      setTimeout(() => setCopiedId(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const clearChat = () => {
    if (messages.length > 0 && window.confirm('Clear all messages?')) {
      setMessages([])
      setError(null)
    }
  }

  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await axios.post<RAGResponse>(`${API_BASE_URL}/api/query`, {
        question: input
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError('Failed to get response. Please make sure the backend server is running.')
      console.error('Error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const exampleQuestions = [
    "What is required to prove criminal intent in indecent exposure cases?",
    "Can a landlord waive a lease covenant by accepting rent?",
    "What are the requirements for a broker to earn commission on a real estate transaction?"
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex flex-col dark relative overflow-hidden">
      {/* Spotlight Effects */}
      <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" fill="white" />

      {/* Header */}
      <header className="bg-slate-900/30 backdrop-blur-md border-b border-slate-800/50 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <motion.div
              className="flex items-center gap-3"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <BackgroundGradient className="rounded-lg p-0.5">
                <div className="bg-slate-950 p-2 rounded-lg">
                  <Scale className="w-6 h-6 text-blue-400" />
                </div>
              </BackgroundGradient>
              <div>
                <h1 className="text-xl font-bold text-white">
                  Legal <Highlight className="text-white">RAG</Highlight> Assistant
                </h1>
                <p className="text-sm text-gray-400">AI-Powered Legal Research</p>
              </div>
            </motion.div>
            {messages.length > 0 && (
              <motion.button
                onClick={clearChat}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg text-gray-300 hover:text-white transition-all border border-slate-700/50"
                title="Clear chat"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Trash2 className="w-4 h-4" />
                <span className="text-sm font-medium">Clear</span>
              </motion.button>
            )}
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {messages.length === 0 ? (
            /* Welcome Screen */
            <motion.div
              className="text-center py-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <BackgroundGradient className="w-24 h-24 rounded-full mx-auto mb-8">
                <div className="bg-slate-950 w-full h-full rounded-full flex items-center justify-center">
                  <BookOpen className="w-12 h-12 text-blue-400" />
                </div>
              </BackgroundGradient>

              <motion.h2
                className="text-4xl md:text-5xl font-bold text-white mb-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.8 }}
              >
                Welcome to <br />
                <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Legal RAG Assistant
                </span>
              </motion.h2>

              <motion.p
                className="text-gray-400 mb-12 max-w-2xl mx-auto text-lg"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.8 }}
              >
                Ask questions about legal cases and get AI-powered answers backed by actual case law.
                <br />
                <span className="text-blue-400 font-semibold">Powered by Claude Sonnet 4.5</span> and{' '}
                <span className="text-purple-400 font-semibold">1,671 legal cases</span>.
              </motion.p>

              <div className="grid gap-4 max-w-2xl mx-auto">
                <p className="text-sm text-gray-500 font-semibold uppercase tracking-wide mb-2">
                  Example Questions
                </p>
                {exampleQuestions.map((question, idx) => (
                  <motion.button
                    key={idx}
                    onClick={() => setInput(question)}
                    className="w-full text-left p-4 bg-slate-900/50 rounded-xl transition-all text-gray-300 hover:text-white border border-slate-700/50 hover:border-blue-500/50"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7 + idx * 0.1, duration: 0.5 }}
                    whileHover={{ scale: 1.01 }}
                  >
                    {question}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          ) : (
            /* Messages */
            <div className="space-y-6">
              {messages.map((message, idx) => (
                <motion.div
                  key={message.id}
                  className={`flex gap-4 ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: idx * 0.05 }}
                >
                  {message.type === 'assistant' && (
                    <BackgroundGradient className="w-8 h-8 rounded-full flex-shrink-0">
                      <div className="w-full h-full rounded-full bg-slate-950 flex items-center justify-center">
                        <Scale className="w-4 h-4 text-blue-400" />
                      </div>
                    </BackgroundGradient>
                  )}

                  <div
                    className={`max-w-3xl ${
                      message.type === 'user'
                        ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl rounded-tr-sm shadow-lg shadow-blue-500/20'
                        : 'bg-slate-900/80 text-gray-200 rounded-2xl rounded-tl-sm border border-slate-800/50 backdrop-blur-sm'
                    } px-6 py-4 relative group`}
                  >
                    {message.type === 'user' ? (
                      <>
                        <p className="text-white">{message.content}</p>
                        <div className="text-xs text-blue-200 mt-2 opacity-70">
                          {formatTimestamp(message.timestamp)}
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div className="text-xs text-gray-500">
                            {formatTimestamp(message.timestamp)}
                          </div>
                          <button
                            onClick={() => copyToClipboard(message.content, message.id)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-slate-700 rounded text-gray-400 hover:text-white"
                            title="Copy answer"
                          >
                            {copiedId === message.id ? (
                              <Check className="w-4 h-4 text-green-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        <div className="markdown-content">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>

                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-6 pt-4 border-t border-slate-700">
                            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                              Sources ({message.sources.length} cases)
                            </h4>
                            <div className="space-y-3">
                              {message.sources.map((source, idx) => (
                                <div
                                  key={idx}
                                  className="bg-slate-900/50 p-3 rounded-lg border border-slate-700/50"
                                >
                                  <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1">
                                      <p className="font-semibold text-blue-400">
                                        {source.case_name}
                                      </p>
                                      <p className="text-sm text-gray-400 mt-1">
                                        {source.citation} • {source.court} • {source.decision_date}
                                      </p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <div className="flex-shrink-0 bg-blue-500/20 px-2 py-1 rounded text-xs font-mono text-blue-400">
                                        {(source.score * 100).toFixed(1)}%
                                      </div>
                                      <button
                                        onClick={() => navigate(`/case/${source.case_id}`)}
                                        className="p-2 hover:bg-slate-800 rounded text-gray-400 hover:text-white transition-colors"
                                        title="View case details"
                                      >
                                        <Eye className="w-4 h-4" />
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  {message.type === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
                      <span className="text-xs font-bold text-white">You</span>
                    </div>
                  )}
                </motion.div>
              ))}

              {isLoading && (
                <motion.div
                  className="flex gap-4 justify-start"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <BackgroundGradient className="w-8 h-8 rounded-full flex-shrink-0">
                    <div className="w-full h-full rounded-full bg-slate-950 flex items-center justify-center">
                      <Scale className="w-4 h-4 text-blue-400" />
                    </div>
                  </BackgroundGradient>
                  <div className="bg-slate-900/80 border border-slate-800/50 backdrop-blur-sm rounded-2xl rounded-tl-sm px-6 py-4">
                    <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}

          {error && (
            <motion.div
              className="mt-4 bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-start gap-3 backdrop-blur-sm"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-400 font-semibold">Error</p>
                <p className="text-red-300 text-sm mt-1">{error}</p>
              </div>
            </motion.div>
          )}
        </div>
      </main>

      {/* Input Area */}
      <div className="border-t border-slate-800/50 bg-slate-900/30 backdrop-blur-md relative z-20">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a legal question..."
                disabled={isLoading}
                className="w-full bg-slate-950/80 border border-slate-800/50 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 disabled:opacity-50 transition-all"
              />
              {!isLoading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-2 text-xs text-gray-600">
                  <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700">Ctrl+K</kbd>
                  <span>to focus</span>
                </div>
              )}
            </div>
            <motion.button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-slate-800 disabled:to-slate-800 disabled:cursor-not-allowed text-white px-6 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all shadow-lg shadow-blue-500/20 disabled:shadow-none"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
              Send
            </motion.button>
          </form>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ChatInterface />} />
        <Route path="/case/:caseId" element={<CaseViewer />} />
      </Routes>
    </Router>
  )
}

export default App
