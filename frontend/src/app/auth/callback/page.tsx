"use client";

import { useEffect, useState } from "react";
import { getCurrentUser, fetchAuthSession } from "@aws-amplify/auth";
import { useRouter } from "next/navigation";

export default function CallbackPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const completeLogin = async () => {
      try {
        // This will fail if the user isn't logged in
        // TODO: don't think getCurrentUser() is actually working rn
        const user = await getCurrentUser();
        console.log("Logged in user:", user);

        const session = await fetchAuthSession();
        console.log("Session:", session);

        router.push("/"); // or /dashboard, wherever your app goes after login
      } catch (err) {
        console.error("Login callback error:", err);
        setError("Something went wrong during login.");
      }
    };

    completeLogin();
  }, [router]);

  if (error) return <p>{error}</p>;
  return <p>Finishing sign-in...</p>;
}
