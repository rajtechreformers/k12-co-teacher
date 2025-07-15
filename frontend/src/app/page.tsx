"use client";
import { useEffect, useState } from "react";
import { getCurrentUser } from "@aws-amplify/auth";
import { useRouter } from "next/navigation";
import DashboardPage from "./dashboard/page";

// TODO: getCurrentUser() needs to be fixed
export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await getCurrentUser();
        // logged in, show dashboard
        setLoading(false);
      } catch {
        router.push("/login");
      }
    };
    checkAuth();
  }, [router]);
  if (loading) return <p>Loading...</p>;
  return (
    <main>
      <DashboardPage />;
    </main>
  );
}
