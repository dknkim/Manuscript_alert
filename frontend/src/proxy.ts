import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import type { NextRequest, NextFetchEvent } from "next/server";

const CLERK_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
const isPublicRoute = createRouteMatcher(["/sign-in(.*)"]);

// clerkMiddleware throws "Missing publishableKey" when invoked without a key,
// even though the handler body guards against it. Build a handler only when
// Clerk is configured; otherwise fall back to a pass-through middleware so
// the app works in CI and local dev without auth.
const clerkHandler = clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export default function middleware(
  req: NextRequest,
  event: NextFetchEvent,
): ReturnType<typeof clerkHandler> {
  if (!CLERK_KEY) return NextResponse.next() as ReturnType<typeof clerkHandler>;
  return clerkHandler(req, event);
}

export const config = {
  matcher: [
    // Skip Next.js internals and static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
