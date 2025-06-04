import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import Navbar from "./components/navbar";
import LoginSignup from "./pages/login-signup";
import Home from "./pages/home";
import Chatbot from "./pages/chatbot";
import FormPage from "./pages/form-page";
import Settings from "./pages/settings";

function App() {

  useEffect(() => {
  fetch("http://localhost:8000/api/v1/chat", {
    method: "POST"
  })
    .then(res => res.json())
    .then(data => console.log(data));
}, []);

  return (
    <Router>
      <Navbar />
      <div className="pt-16">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/home" element={<Home />} />
          <Route path="/login" element={<LoginSignup />} />
          <Route path="/chat" element={<Chatbot />} />
          <Route path="/form" element={<FormPage />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;