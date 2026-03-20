/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: "export" — enable for production static builds (S3 + CloudFront)
  // Removed for dev to allow dynamic [id] routes without generateStaticParams
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
