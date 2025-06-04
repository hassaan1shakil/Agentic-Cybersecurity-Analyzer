import { Link } from 'react-router-dom'; // Use this instead of 'next/link'
import { MessageSquare, FileText, Settings } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="bg-white w-[100vw]">
      <div className="mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-black mb-4">Welcome to MVP</h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            A simple and powerful platform designed to streamline your workflow. Chat with AI, manage your projects, and
            configure everything to your needs.
          </p>
          <div className="flex gap-4 justify-center">
            <Link to="/chat" className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">
              Start Chatting
            </Link>
            <Link to="/form" className="border border-black px-4 py-2 rounded hover:bg-gray-100">
              Submit Project
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="mb-4">
              <MessageSquare className="h-8 w-8 mb-2" />
              <h3 className="text-lg font-semibold">AI Chat</h3>
              <p className="text-gray-600 text-sm">
                Interact with our intelligent chatbot to get instant answers and assistance.
              </p>
            </div>
            <Link to="/chat" className="block border border-black px-4 py-2 text-center rounded hover:bg-gray-100">
              Open Chat
            </Link>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <div className="mb-4">
              <FileText className="h-8 w-8 mb-2" />
              <h3 className="text-lg font-semibold">Project Submission</h3>
              <p className="text-gray-600 text-sm">
                Submit your projects with website links, GitHub repos, or local files.
              </p>
            </div>
            <Link to="/form" className="block border border-black px-4 py-2 text-center rounded hover:bg-gray-100">
              Submit Project
            </Link>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <div className="mb-4">
              <Settings className="h-8 w-8 mb-2" />
              <h3 className="text-lg font-semibold">Settings</h3>
              <p className="text-gray-600 text-sm">
                Customize your experience and manage your account preferences.
              </p>
            </div>
            <Link to="/settings" className="block border border-black px-4 py-2 text-center rounded hover:bg-gray-100">
              Open Settings
            </Link>
          </div>
        </div>

        {/* About Section */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-black mb-4">About MVP</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Our platform combines the power of AI with intuitive project management tools. Whether you're looking to get
            quick answers through our chatbot or submit and manage your projects, we've got you covered with a clean,
            simple interface.
          </p>
        </div>
      </div>
    </div>
  );
}
