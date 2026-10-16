/** Public demo build: set NEXT_PUBLIC_DEMO_ONLY=1 when deploying just the landing page (no backend, no local model).
 *  Calls to action then point at the in-page studio, and the app routes redirect home. */
export const DEMO_ONLY = process.env.NEXT_PUBLIC_DEMO_ONLY === "1";
export const APP = DEMO_ONLY ? "#studio" : "/create";
