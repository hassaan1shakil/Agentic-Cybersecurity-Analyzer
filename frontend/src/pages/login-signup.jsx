import { useState } from "react"
import { useNavigate } from "react-router-dom"

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    // Validation for signup
    if (!isLogin && password !== confirmPassword) {
      setError("Passwords do not match")
      setLoading(false)
      return
    }

    try {
      const endpoint = isLogin ? "/login" : "/signup"
      const response = await fetch(`http://192.168.46.212:8080/api/v1/auth${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Authentication failed")
      }

      // Store email in localStorage
      localStorage.setItem("userEmail", data.email)
      
      // Redirect to home page
      navigate("/home")

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-[100vw] bg-white px-4 pt-16">
      <div className="w-full max-w-md mx-auto border border-gray-300 rounded-md shadow-md p-8">
        <header className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-black mb-1">
            {isLogin ? "Sign In" : "Sign Up"}
          </h1>
          <p className="text-gray-600 text-sm">
            {isLogin
              ? "Enter your credentials to access your account"
              : "Create a new account to get started"}
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="email" className="block mb-1 text-sm font-medium text-black">
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full border border-gray-400 rounded px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>

          <div>
            <label htmlFor="password" className="block mb-1 text-sm font-medium text-black">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border border-gray-400 rounded px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>

          {!isLogin && (
            <div>
              <label htmlFor="confirmPassword" className="block mb-1 text-sm font-medium text-black">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full border border-gray-400 rounded px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-black"
              />
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-black text-white py-2 rounded hover:bg-gray-800 transition"
            disabled={loading}
          >
            {loading ? "Please wait..." : isLogin ? "Sign In" : "Sign Up"}
          </button>

          {error && (
            <div className="mt-4 text-sm text-red-600 text-center">
              {error}
            </div>
          )}
        </form>

        <div className="mt-4 text-center text-sm text-gray-700">
          {isLogin ? (
            <>
              {"Don't have an account? "}
              <button
                onClick={() => setIsLogin(false)}
                className="underline hover:text-gray-900 cursor-pointer"
                type="button"
              >
                Sign up
              </button>
            </>
          ) : (
            <>
              {"Already have an account? "}
              <button
                onClick={() => setIsLogin(true)}
                className="underline hover:text-gray-900 cursor-pointer"
                type="button"
              >
                Sign in
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
