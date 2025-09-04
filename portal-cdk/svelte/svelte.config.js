import adapter from "@sveltejs/adapter-static";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    paths: {
      base: "/ui", // Make sure prefix matches portal_cdk_stack.py/FRONTEND_PREFIX
      relative: false, // Explicitly set to false so adpater-static doesn't strip prefixes
    },
    adapter: adapter({
      // default options are shown. On some platforms
      // these options are set automatically — see below
      pages: "build",
      assets: "build",
      fallback: "200.html",
      precompress: false,
      strict: true,
    }),
  },
};

export default config;
