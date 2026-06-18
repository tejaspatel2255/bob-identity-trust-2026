/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: [
    'react-force-graph-2d',
    'react-kapsule',
    'kapsule',
    'canvas-color-tracker',
    'd3-force',
    'd3-selection',
    'd3-zoom'
  ]
};

export default nextConfig;
