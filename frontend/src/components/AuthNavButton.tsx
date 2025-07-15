"use client";

import { useEffect, useState } from "react";
import { getCurrentUser, signInWithRedirect, signOut } from "@aws-amplify/auth";

export default function AuthNavButton() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await getCurrentUser();
        setIsAuthenticated(true);
      } catch {
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = () => signInWithRedirect();
  const handleLogout = () => signOut({ global: true });

  if (isAuthenticated === null) return null; // optional: show loading indicator

  return isAuthenticated ? (
    <button
      onClick={handleLogout}
      className="text-sm text-blue-600 hover:underline"
    >
      Sign out
    </button>
  ) : (
    <button
      onClick={handleLogin}
      className="text-sm text-blue-600 hover:underline"
    >
      Log in
    </button>
  );
}
