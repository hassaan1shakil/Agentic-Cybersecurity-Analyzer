import { useState } from "react"
import { LinkIcon, FileText, GitFork } from "lucide-react"
import { useNavigate } from "react-router-dom"

export default function FormPage() {
    const [websiteLink, setWebsiteLink] = useState("")
    const [githubRepo, setGithubRepo] = useState("")
    // const [localPath, setLocalPath] = useState("")
    const [textContent, setTextContent] = useState("")
    const [error, setError] = useState("")
    const [success, setSuccess] = useState("")
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError("")
        setSuccess("")
        setLoading(true)

        if (!websiteLink && !githubRepo) {
            setError("Please provide at least one source: Website Link, GitHub Repo, or Local Directory.")
            setLoading(false)
            return
        }

        const userEmail = localStorage.getItem("userEmail") || "unknown"

        const payload = {
            website_url: websiteLink || null,
            github_url: githubRepo || null,
            // local_path: localPath || null,
            email: userEmail,   // maybe just send the user_id as the jwt token will be sent
        }

        try {
            const response = await fetch("http://192.168.46.212:8080/api/submit-form", { //change the api endpoint
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
            if (!response.ok) {
                const data = await response.json()
                throw new Error(data.detail || "Submission failed")
            }
            const data = await response.json()
            const process_id = data.id || "unknown"

            localStorage.setItem("process_id", process_id)
            console.log("Process ID:", process_id)
            setSuccess("Form submitted successfully!")
            setLoading(false)

            // maybe show user a pop up saying that their report will be generated soon, and redirect to reports page to check updates. or incorporate them in the chatbot page
            // Pass response data to chatbot page using state
            navigate("/chat", { state: { backendResponse: data } })
        } catch (err) {
            setError(err.message)
            setLoading(false)
        }
    }

    return (
        <div className="w-[100vw] bg-white py-12">
            <div className="mx-auto px-4">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-black mb-2">Submit Your Project</h1>
                    <p className="text-gray-600">Provide your project details using any of the methods below</p>
                </div>

                <div className="border rounded-lg shadow-md p-6">
                    <header className="mb-4">
                        <h2 className="text-xl font-semibold">Project Information</h2>
                        <p className="text-gray-500 text-sm">Fill in the relevant fields for your project submission</p>
                    </header>

                    <form onSubmit={handleSubmit} className="space-y-6 text-black">
                        {/* Website Link */}
                        <div className="space-y-1">
                            <label htmlFor="website" className="flex items-center gap-2 text-sm font-medium text-gray-700">
                                <LinkIcon className="h-4 w-4" />
                                Website Link
                            </label>
                            <input
                                id="website"
                                type="url"
                                placeholder="https://example.com"
                                value={websiteLink}
                                onChange={(e) => setWebsiteLink(e.target.value)}
                                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>

                        {/* GitHub Repo Link */}
                        <div className="space-y-1">
                            <label htmlFor="github" className="flex items-center gap-2 text-sm font-medium text-gray-700">
                                <GitFork className="h-4 w-4" />
                                GitHub Repository Link
                            </label>
                            <input
                                id="github"
                                type="url"
                                placeholder="https://github.com/username/repository"
                                value={githubRepo}
                                onChange={(e) => setGithubRepo(e.target.value)}
                                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>

                        {/* Local Directory Path (Manual Input) */}
                        {/* <div className="space-y-1">
                            <label htmlFor="localPath" className="flex items-center gap-2 text-sm font-medium text-gray-700">
                                <FileText className="h-4 w-4" />
                                Local Directory Path
                            </label>
                            <input
                                id="localPath"
                                type="text"
                                placeholder="/absolute/path/to/your/project"
                                value={localPath}
                                onChange={(e) => setLocalPath(e.target.value)}
                                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                        </div> */}

                        {/* Textarea */}
                        <div className="space-y-1">
                            <label htmlFor="text" className="flex items-center gap-2 text-sm font-medium text-gray-700">
                                <FileText className="h-4 w-4" />
                                Report Details
                            </label>
                            <textarea
                                id="text"
                                placeholder="Specify the details about your desired report..."
                                value={textContent}
                                onChange={(e) => setTextContent(e.target.value)}
                                rows={4}
                                required
                                className="w-full rounded-md border border-gray-300 px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>

                        {error && <div className="text-red-600 text-sm">{error}</div>}
                        {success && <div className="text-green-600 text-sm">{success}</div>}

                        <button
                            type="submit"
                            className="w-full bg-black text-white font-semibold rounded-md px-4 py-2 hover:bg-gray-800 transition-colors"
                            disabled={loading}
                        >
                            {loading ? "Submitting..." : "Submit Project"}
                        </button>
                        {loading && (
                            <div className="flex justify-center items-center mt-4">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                                <span className="ml-2 text-gray-700">Processing...</span>
                            </div>
                        )}
                    </form>
                </div>
            </div>
        </div>
    )
}
