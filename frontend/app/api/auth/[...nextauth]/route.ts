import NextAuth, { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  pages: {
    signIn: "/",
  },
  callbacks: {
    async session({ session, token }) {
      if (token.vitaUserId)   session.vitaUserId   = token.vitaUserId   as string;
      if (token.vitaUserName) session.vitaUserName = token.vitaUserName as string;
      if (token.vitaPersona)  session.vitaPersona  = token.vitaPersona  as string;
      // Expose the Google sub so the onboarding page can use it as sso_id
      if (token.googleSub)    session.googleSub    = token.googleSub    as string;
      return session;
    },
    async jwt({ token, account, profile }) {
      // Store the stable Google account ID (sub) on first sign-in
      if (account?.provider === "google" && account.providerAccountId) {
        token.googleSub = account.providerAccountId;
      }
      // Look up the user in our backend on first sign-in
      if (account?.provider === "google" && profile?.email) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
        try {
          const res = await fetch(
            `${apiUrl}/users/by-email/${encodeURIComponent(profile.email)}`
          );
          if (res.ok) {
            const data = await res.json();
            token.vitaUserId = data.user_id;
            token.vitaUserName = data.full_name;
            token.vitaPersona = data.persona ?? "friend";
          }
          // 404 means the user needs onboarding — vitaUserId stays undefined
        } catch {
          // Backend unreachable — proceed without vita fields
        }
      }
      return token;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
