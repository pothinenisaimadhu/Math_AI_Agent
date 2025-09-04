import React, { useState } from "react";
import { motion } from "framer-motion";
import { Send, Loader2, Bot, User } from "lucide-react";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!question.trim()) return;

    // Add user message
    const newMessages = [
      ...messages,
      { type: "user", text: question, id: Date.now() },
    ];
    setMessages(newMessages);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "demo", question }),
      });

      const data = await res.json();
      setMessages([
        ...newMessages,
        {
          type: "bot",
          text: data.error
            ? `Error: ${data.error}`
            : data.answer || "No answer provided",
          id: Date.now() + 1,
        },
      ]);
    } catch (error) {
      setMessages([
        ...newMessages,
        { type: "bot", text: `Error: ${error.message}`, id: Date.now() + 1 },
      ]);
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-indigo-100 via-white to-purple-100">
      {/* Header */}
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="p-6 text-center shadow-md bg-white z-10"
      >
        <h1 className="text-3xl font-bold text-indigo-600">Math AI Tutor</h1>
        <p className="text-gray-500">Ask me any math problem!</p>
      </motion.div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex items-start gap-3 ${
              msg.type === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {msg.type === "bot" && (
              <div className="p-2 bg-indigo-100 rounded-full">
                <Bot className="w-5 h-5 text-indigo-600" />
              </div>
            )}

            <div
              className={`p-3 rounded-2xl max-w-md shadow ${
                msg.type === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-white border text-gray-800"
              }`}
            >
              {msg.text}
            </div>

            {msg.type === "user" && (
              <div className="p-2 bg-indigo-600 rounded-full">
                <User className="w-5 h-5 text-white" />
              </div>
            )}
          </motion.div>
        ))}

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2 text-gray-500"
          >
            <Loader2 className="w-5 h-5 animate-spin" />
            Thinking...
          </motion.div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white shadow-md">
        <div className="flex items-center gap-2">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your math question..."
            rows={1}
            className="flex-1 resize-none border rounded-xl p-3 focus:ring-2 focus:ring-indigo-400 outline-none"
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !question.trim()}
            className="p-3 bg-indigo-600 text-white rounded-xl shadow hover:bg-indigo-700 transition"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send />}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
