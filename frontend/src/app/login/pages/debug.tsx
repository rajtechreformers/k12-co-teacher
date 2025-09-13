"use client";

import { useAuth } from "react-oidc-context";

export default function DebugPage() {
  const auth = useAuth();

  if (!auth.isAuthenticated) {
    return <p>❌ Not logged in</p>;
  }

  return (
    <div style={{ whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
      <h2>✅ Authenticated</h2>
      <h3>Tokens:</h3>
      <pre>{JSON.stringify(auth.user, null, 2)}</pre>
    </div>
  );
}
