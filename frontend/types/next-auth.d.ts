import "next-auth";

declare module "next-auth" {
  interface Session {
    vitaUserId?: string;
    vitaUserName?: string;
    vitaPersona?: string;
    googleSub?: string;
  }
}
