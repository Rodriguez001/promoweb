/** @type {import('next').NextConfig} */
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development'
})

const nextConfig = {
  // experimental: {
  //   appDir: true, // No longer needed in Next.js 14
  // },
  // output: 'standalone', // Disabled for development
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.amazonaws.com',
      },
      {
        protocol: 'https',
        hostname: '**.cloudinary.com',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  typescript: {
    // Type checking is handled by GitHub Actions
    ignoreBuildErrors: false,
  },
  eslint: {
    // ESLint is run in GitHub Actions
    ignoreDuringBuilds: true,
  },
}

module.exports = withPWA(nextConfig)
