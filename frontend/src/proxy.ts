import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const isPublicRoute = createRouteMatcher(["/sign-in(.*)"]);

/**
 * If NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is set, protect all routes except /sign-in.
 * If not set (local dev without auth), allow everything through.
 */
export default process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  ? clerkMiddleware((auth, req) => {
      if (!isPublicRoute(req)) {
        auth.protect();
      }
    })
  : (_req: NextRequest) => NextResponse.next();

export const config = {
  matcher: [
    // Skip Next.js internals and static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
