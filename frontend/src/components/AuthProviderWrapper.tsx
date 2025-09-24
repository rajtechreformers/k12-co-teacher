"use client";

import { AuthProvider } from "react-oidc-context";
import { ReactNode } from "react";

const redirectUri =
  process.env.NEXT_PUBLIC_REDIRECT_URI ||
  (typeof window !== "undefined" ? window.location.origin : "");

const cognitoAuthConfig = {
  authority: `https://cognito-idp.${process.env.NEXT_PUBLIC_COGNITO_REGION}.amazonaws.com/${process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID}`,
  client_id: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || "",
  redirect_uri: redirectUri,
  post_logout_redirect_uri: redirectUri,
  response_type: "code",
  scope: "openid email",
  automaticSilentRenew: false,
  loadUserInfo: false,
};

export default function AuthProviderWrapper({
  children,
}: {
  children: ReactNode;
}) {
  return <AuthProvider {...cognitoAuthConfig}>{children}</AuthProvider>;
}