/** @type {import('next').NextConfig} */
const nextConfig = {
  // In development, proxy /api/* to the local backend so we don't need
  // NEXT_PUBLIC_API_URL set. In production (Vercel), the frontend calls
  // the Railway backend URL directly via NEXT_PUBLIC_API_URL.
  ...(process.env.NODE_ENV === "development" && {
    async rewrites() {
      return [
        {
          source: "/api/:path*",
          destination: "http://localhost:8000/api/:path*",
        },
      ];
    },
  }),
};

export default nextConfig;
