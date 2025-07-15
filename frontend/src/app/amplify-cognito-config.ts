"use client";
import {Amplify, type ResourcesConfig} from "aws-amplify";
import "@aws-amplify/auth";

export const authConfig: ResourcesConfig["Auth"] = {
    Cognito:{
        userPoolId: String(process.env.NEXT_PUBLIC_USER_POOL_ID),
        userPoolClientId : String(process.env.NEXT_PUBLIC_USER_POOL_CLIENT_ID),
        loginWith: {
            oauth: {
              domain: "us-west-2quusm9gav.auth.us-west-2.amazoncognito.com", 
              scopes: ["email", "openid"],
              redirectSignIn: ["http://localhost:3000/auth/callback"],
              redirectSignOut: ["http://localhost:3000/"],
              responseType: "code", // or "token" (code is recommended)
            },
          },
    }, 

};
Amplify.configure(
    {
        Auth: authConfig,
    },
    // server side rendering : makes sure amplify uses cookies for state storage
    {ssr: true} 

);
console.log("Amplify has been configured on the client");

export default function ConfigureAmplifyClientSide(){
    return null;
}