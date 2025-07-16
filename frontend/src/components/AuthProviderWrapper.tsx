"use client";

import { AuthProvider } from "react-oidc-context";
import { ReactNode } from "react";

const cognitoAuthConfig = {
  authority: "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_aHDFq5X7H",
  client_id: "5ua1aurvnmtc49a9409depmump",
  redirect_uri: typeof window !== "undefined" ? window.location.origin : "",
  post_logout_redirect_uri: typeof window !== "undefined" ? window.location.origin : "",
  response_type: "code",
  scope: "openid email",
  automaticSilentRenew: false,
  loadUserInfo: false,
};

export default function AuthProviderWrapper({ children }: { children: ReactNode }) {
  return <AuthProvider {...cognitoAuthConfig}>{children}</AuthProvider>;
}
