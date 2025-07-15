// frontend/src/app/login
"use client";

import { signInWithRedirect } from "aws-amplify/auth";

export default function LoginPage() {
  const handleLogin = () => {
    console.log("Login button clicked");
    try {
      signInWithRedirect();
    } catch (err) {
      console.error("Redirect failed:", err);
    }
  };

  return (
    <main className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-2xl font-bold mb-4">Login</h1>
      <button
        onClick={handleLogin}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        Sign in with Cognito
      </button>
    </main>
  );
}
