/** @type {import('next').NextConfig} */
const nextConfig = {
  images: { unoptimized: true },
  transpilePackages: [
    "react-markdown",
    "remark-gfm",
    "remark-parse",
    "unified",
    "bail",
    "is-plain-obj",
    "trough",
    "vfile",
    "vfile-message",
    "unist-util-stringify-position",
    "mdast-util-from-markdown",
    "mdast-util-to-string",
    "micromark",
    "decode-named-character-reference",
    "character-entities",
    "mdast-util-to-hast",
    "trim-lines",
    "unist-util-is",
    "unist-util-visit",
    "unist-util-visit-parents",
    "hast-util-to-jsx-runtime",
    "hast-util-whitespace",
    "property-information",
    "space-separated-tokens",
    "comma-separated-tokens",
    "remark-rehype",
    "rehype-raw",
    "hast-util-raw",
    "hast-util-from-parse5",
    "hast-util-to-parse5",
    "hastscript",
    "html-void-elements",
    "zwitch",
  ],
  async rewrites() {
    const backend = 'http://127.0.0.1:8000';
    // 前端用相对路径直接调用后端接口，经由 Next.js 转发。
    // 每个后端根级路径前缀都必须登记在这里，漏登记的前缀会被 Next.js 自身
    // 处理并返回 404（此前 /analyze、/agent/*、/report/* 等即因此不可达）。
    const routes = [
      '/api/:path*',        // models / setup / health/full / permissions
      '/auth/:path*',
      '/admin/:path*',
      '/agent/:path*',      // chat · chat/stream · sessions · init_session
      '/chat/:path*',       // 统一流式对话入口
      '/analyze/:path*',    // /analyze 与 /analyze/stream
      '/classify',
      '/replacement',
      '/select-part',
      '/interpret-selection',
      '/report/:path*',
      '/upload/:path*',
      '/bom/:path*',
      '/export/:path*',
      '/recalculate',
      '/workflow/:path*',
      '/schematic/:path*',
      '/health',
      '/models/:path*',
      '/sessions/:path*',
      '/mpn/:path*',
    ];
    return routes.map(source => ({
      source,
      destination: `${backend}${source}`,
    }));
  },
};

module.exports = nextConfig;
