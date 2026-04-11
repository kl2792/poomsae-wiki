import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/poomsae-wiki",
  assetPrefix: "/poomsae-wiki",
  images: { unoptimized: true },
};

export default nextConfig;
