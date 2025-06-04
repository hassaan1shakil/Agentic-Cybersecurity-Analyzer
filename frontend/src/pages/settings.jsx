import { useState } from "react"
import { User, Bell, Shield, Trash2 } from "lucide-react"

export default function SettingsPage() {
    const [name, setName] = useState("")
    const [email, setEmail] = useState("")
    const [notifications, setNotifications] = useState(true)
    const [emailUpdates, setEmailUpdates] = useState(false)
    const [twoFactor, setTwoFactor] = useState(false)

    const handleSave = () => {
        alert("Settings saved successfully!")
    }

    const handleDeleteAccount = () => {
        if (
            window.confirm(
                "Are you sure you want to delete your account? This action cannot be undone."
            )
        ) {
            alert("Account deletion requested.")
        }
    }

    return (
        <div className="min-h-screen w-[100vw] bg-white py-12">
            <div className="mx-auto max-w-2xl px-4">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-black mb-2">Settings</h1>
                    <p className="text-gray-600">
                        Manage your account preferences and security settings
                    </p>
                </div>

                <div className="space-y-6">
                    {/* Profile Settings */}
                    <section className="border rounded shadow p-6">
                        <header className="mb-4">
                            <h2 className="flex items-center gap-2 text-xl font-semibold">
                                <User className="h-5 w-5" />
                                Profile Information
                            </h2>
                            <p className="text-gray-500">
                                Update your personal information and contact details
                            </p>
                        </header>
                        <div className="space-y-4 text-black">
                            <div>
                                <label htmlFor="name" className="block mb-1 font-medium">
                                    Full Name
                                </label>
                                <input
                                    id="name"
                                    placeholder="John Doe"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full border rounded px-3 py-2"
                                />
                            </div>
                            <div>
                                <label htmlFor="email" className="block mb-1 font-medium">
                                    Email Address
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    placeholder="john.doe@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full border rounded px-3 py-2"
                                />
                            </div>
                        </div>
                    </section>

                    {/* Notification Settings */}
                    <section className="border rounded shadow p-6">
                        <header className="mb-4">
                            <h2 className="flex items-center gap-2 text-xl font-semibold">
                                <Bell className="h-5 w-5" />
                                Notifications
                            </h2>
                            <p className="text-gray-500">
                                Configure how you want to receive notifications
                            </p>
                        </header>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <label className="font-medium">Push Notifications</label>
                                    <p className="text-sm text-gray-500">
                                        Receive notifications in your browser
                                    </p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={notifications}
                                    onChange={() => setNotifications(!notifications)}
                                    className="h-5 w-5"
                                />
                            </div>
                            <hr />
                            <div className="flex items-center justify-between">
                                <div>
                                    <label className="font-medium">Email Updates</label>
                                    <p className="text-sm text-gray-500">
                                        Receive updates and newsletters via email
                                    </p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={emailUpdates}
                                    onChange={() => setEmailUpdates(!emailUpdates)}
                                    className="h-5 w-5"
                                />
                            </div>
                        </div>
                    </section>

                    {/* Security Settings */}
                    <section className="border rounded shadow p-6">
                        <header className="mb-4">
                            <h2 className="flex items-center gap-2 text-xl font-semibold">
                                <Shield className="h-5 w-5" />
                                Security
                            </h2>
                            <p className="text-gray-500">
                                Manage your account security and privacy settings
                            </p>
                        </header>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <label className="font-medium">Two-Factor Authentication</label>
                                    <p className="text-sm text-gray-500">
                                        Add an extra layer of security to your account
                                    </p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={twoFactor}
                                    onChange={() => setTwoFactor(!twoFactor)}
                                    className="h-5 w-5"
                                />
                            </div>
                            <hr />
                            <div>
                                <label className="font-medium block mb-2">Change Password</label>
                                <button className="w-full border border-gray-400 rounded py-2 hover:bg-gray-100">
                                    Update Password
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* Danger Zone */}
                    <section className="border rounded shadow p-6 border-red-200">
                        <header className="mb-4">
                            <h2 className="flex items-center gap-2 text-xl font-semibold text-red-600">
                                <Trash2 className="h-5 w-5" />
                                Danger Zone
                            </h2>
                            <p className="text-red-500">Irreversible and destructive actions</p>
                        </header>
                        <button
                            onClick={handleDeleteAccount}
                            className="w-full bg-red-600 text-white rounded py-2 hover:bg-red-700"
                        >
                            Delete Account
                        </button>
                    </section>

                    {/* Save Button */}
                    <div className="flex justify-end">
                        <button
                            onClick={handleSave}
                            className="bg-black text-white rounded px-6 py-2 hover:bg-gray-800"
                        >
                            Save Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
