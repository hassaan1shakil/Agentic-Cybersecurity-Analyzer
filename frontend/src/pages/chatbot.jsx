// import { GoogleGenerativeAI } from "@google/generative-ai";
import { useState, useEffect, useCallback, useRef } from "react";
import { Send, Plus, MessageSquare } from "lucide-react";
import axios from "axios";
import { GoogleGenAI } from "@google/genai";

export default function ChatPage() {
    // Dummy summary (will be fetched later)
    const [summary, setSummary] = useState(
        "hey this is a summary of the security analysis results. It includes findings, recommendations, and potential vulnerabilities identified during the analysis. The summary is designed to provide a quick overview of the security posture and areas that may require further attention or remediation."
    );
    const [selectedText, setSelectedText] = useState("");
    const [showExplainButton, setShowExplainButton] = useState(false);
    const [buttonPosition, setButtonPosition] = useState({ x: 0, y: 0 });
    const [loading, setLoading] = useState(false);

    const [messages, setMessages] = useState([
        {
            id: "1",
            content: "Hello! How can I help you today?",
            isUser: false,
            timestamp: new Date(),
        },
    ]);

    const [inputValue, setInputValue] = useState("");

    const [chatSessions] = useState([
        { id: "1", title: "General Questions", lastMessage: new Date() },
        {
            id: "2",
            title: "Project Help",
            lastMessage: new Date(Date.now() - 86_400_000),
        },
        {
            id: "3",
            title: "Technical Support",
            lastMessage: new Date(Date.now() - 172_800_000),
        },
    ]);

    const [isPlaying, setIsPlaying] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    const audioRef = useRef(null);

    // Initialize Gemini client
    const ai = new GoogleGenAI({ apiKey: "API_KEY" });

    const handleTextSelection = () => {
        const selection = window.getSelection();
        const text = selection.toString().trim();

        if (text) {
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            setSelectedText(text);
            setButtonPosition({
                x: rect.left + (rect.width / 2),
                y: rect.top + scrollTop - 40, // Account for scroll position
            });
            setShowExplainButton(true);
        } else {
            setShowExplainButton(false);
        }
    };

    async function translateToUrdu(text) {
        try {
            const prompt = `
Translate the following text into very simple and easy-to-understand Urdu.

Instructions:
- Do not include links, references, or vulnerability names.
- Just convert the explanation part into natural, simplified Urdu.
- Avoid technical jargon and keep the tone friendly and easy for non-experts.

Text to translate:
${text}
`;

            const result = await ai.models.generateContent({
                model: "gemini-2.0-flash",
                contents: prompt,
            });

            const response = await result.response;
            return response.text().trim();
        } catch (error) {
            console.error("Translation error:", error);
            return "ترجمہ میں خرابی ہو گئی۔";
        }
    }

    async function convertTextToSpeech(textChunk) {

        const url = "https://api.upliftai.org/v1/synthesis/text-to-speech";

        const payload = {
            voiceId: "v_8eelc901",
            text: textChunk,
            outputFormat: "MP3_22050_128",
        };

        try {
            const response = await axios.post(url, payload, {
                headers: {
                    Authorization: `Bearer API KEY`,
                    "Content-Type": "application/json",
                },
                responseType: "arraybuffer",
            });

            const audioDuration = response.headers["x-uplift-ai-audio-duration"];
            console.log(`Audio duration: ${audioDuration}ms`);

            // Create a blob URL directly from the binary data
            const blob = new Blob([response.data], { type: "audio/mpeg" });
            const blobUrl = URL.createObjectURL(blob);
            return blobUrl;
        } catch (error) {
            console.error("TTS error:", error.response?.data || error.message);
            return null;
        }
    }

    const handleExplain = async () => {
        console.log("Explain button clicked", { selectedText });
        if (!selectedText) {
            console.log("No text selected");
            return;
        }

        setLoading(true);
        console.log("Starting translation process");
        try {
            // Check for required data
            // const userEmail = localStorage.getItem("userEmail");
            // const process_id = localStorage.getItem("process_id");

            // if (!userEmail || !process_id) {
            //     throw new Error("Missing user credentials");
            // }

            // 1. Translate selected text to simple Urdu
            const translatedText = await translateToUrdu(selectedText);
            if (!translatedText) {
                throw new Error("Translation failed");
            }

            // 2. Convert translated Urdu to speech
            const url = await convertTextToSpeech(translatedText);
            if (!url) {
                throw new Error("Text-to-speech conversion failed");
            }

            setAudioUrl(url);
            // Display translated text alongside original
            setSelectedText(`${selectedText}\n\nUrdu Translation:\n${translatedText}`);
        } catch (error) {
            console.error("Error in handleExplain:", error);
            // Add user feedback for errors
            alert(error.message || "Failed to process explanation");
        } finally {
            setLoading(false);
            setShowExplainButton(false);
        }
    };

    // Close explain button when clicking outside
    const handleClickOutside = useCallback((e) => {
        if (!e.target.closest(".summary-content")) {
            setShowExplainButton(false);
        }
    }, []);

    useEffect(() => {
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [handleClickOutside]);

    const handleKeyPress = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleGetSummary = async () => {
        try {
            // Get email from localStorage
            const userEmail = localStorage.getItem("userEmail");
            const process_id = localStorage.getItem("process_id");

            if (!userEmail || !process_id) {
                throw new Error("Missing user email or process ID");
            }

            // Create URL with query parameters
            const url = new URL("http://192.168.46.212:8080/api/get");
            url.searchParams.append("user_id", userEmail);
            url.searchParams.append("filename", "summary.txt");
            url.searchParams.append("process_id", process_id);

            const response = await fetch(url, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            if (!response.ok) {
                throw new Error("Failed to get summary");
            }

            const data = await response.json();
            const response_summary = data.content || "No summary available.";
            setSummary(response_summary);
        } catch (error) {
            console.error("Error:", error);
        }
    };

    // Add cleanup for blob URL
    useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.src = '';
            }
            if (audioUrl) {
                URL.revokeObjectURL(audioUrl);
            }
        };
    }, [audioUrl]);

    const handleSendMessage = () => {
        if (!inputValue.trim()) return;

        const newMessage = {
            id: Date.now().toString(),
            content: inputValue,
            isUser: true,
            timestamp: new Date(),
        };
        setMessages((msgs) => [...msgs, newMessage]);
        setInputValue("");
        // You can then send this to your chat API if needed
    };

    return (
        <div className="flex w-[100vw] bg-white">
            {/* Sidebar */}
            <div className="w-80 border-r border-gray-200 bg-gray-50">
                <div className="p-4">
                    <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-black text-white rounded hover:bg-gray-800">
                        <Plus className="h-4 w-4" />
                        New Summary
                    </button>
                </div>
                <div className="overflow-y-auto h-[calc(100vh-8rem)] px-4 space-y-2">
                    <h3 className="font-semibold text-sm text-gray-600 mb-3">
                        Summary History
                    </h3>
                    {chatSessions.map((session) => (
                        <div
                            key={session.id}
                            className="border rounded-lg p-3 hover:bg-gray-100 cursor-pointer"
                        >
                            <div className="flex items-start gap-3">
                                <MessageSquare className="h-4 w-4 mt-1 text-gray-500" />
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-black truncate">
                                        {session.title}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {session.lastMessage.toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Summary Area */}
            <div className="flex-1 flex flex-col">
                <div className="flex justify-between border-b border-gray-200 p-4">
                    <h1 className="text-xl font-semibold text-black">
                        Security Analysis Summary
                    </h1>

                    <div className="flex gap-2">
                        <button
                            className="w-8vw flex items-center justify-center gap-2 px-4 py-2 bg-black text-white rounded hover:bg-gray-800"
                            onClick={handleGetSummary}
                        >
                            Get Summary
                        </button>

                        <button
                            className="w-8vw flex items-center justify-center gap-2 px-4 py-2 bg-black text-white rounded hover:bg-gray-800"
                            onClick={handleExplain}
                        >
                            Explain Text
                        </button>

                    </div>

                </div>

                <div className="flex-1 overflow-y-auto p-4 relative">
                    <div
                        className="max-w-3xl mx-auto summary-content"
                        onMouseUp={handleTextSelection}
                    >
                        <div className="bg-white rounded-lg shadow-md p-6">
                            <h2 className="text-lg font-semibold mb-4">
                                Analysis Results
                            </h2>
                            <div className="prose prose-sm select-text">
                                {summary.split("\n").map(
                                    (paragraph, index) =>
                                        paragraph.trim() && (
                                            <p key={index} className="mb-4 text-gray-700">
                                                {paragraph}
                                            </p>
                                        )
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Floating Explain Button */}
                    {/* {showExplainButton && (
                        <div
                            className="fixed z-50 transform -translate-x-1/2"
                            style={{
                                left: buttonPosition.x,
                                top: buttonPosition.y,
                            }}
                        >
                            <button
                                className="bg-black text-white px-4 py-2 rounded-full shadow-lg hover:bg-gray-800 transition-colors"
                                onClick={handleExplain}
                                disabled={loading}
                            >
                                {loading ? "..." : "Explain"}
                            </button>
                        </div>
                    )} */}

                    {/* Audio Controls */}
                    {audioUrl && (
                        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
                            <div className="bg-white rounded-lg shadow-lg p-4 flex items-center gap-4">
                                <audio
                                    ref={audioRef}
                                    src={audioUrl}
                                    onEnded={() => setIsPlaying(false)}
                                    className="hidden"
                                />
                                <button
                                    onClick={() => {
                                        if (isPlaying) {
                                            audioRef.current.pause();
                                        } else {
                                            audioRef.current.play();
                                        }
                                        setIsPlaying(!isPlaying);
                                    }}
                                    className="bg-black text-white px-4 py-2 rounded-full hover:bg-gray-800 transition-colors flex items-center gap-2"
                                >
                                    {isPlaying ? (
                                        <>
                                            <span className="w-4 h-4">⏸</span>
                                            Pause
                                        </>
                                    ) : (
                                        <>
                                            <span className="w-4 h-4">▶️</span>
                                            Play Explanation
                                        </>
                                    )}
                                </button>
                                <div className="text-sm text-gray-500">
                                    {Math.floor(audioRef.current?.duration || 0)}s
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
