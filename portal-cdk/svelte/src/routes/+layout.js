export const prerender = true;

// https://svelte.dev/tutorial/kit/trailingslash
// It's important to always have trailing slashes.
// This helps enforce the rule within cloudfront that endpoint /home will aliased with /home/index.html
// If set to "never", /home would become home.html which would be harder to parse and look not as clean
export const trailingSlash = "always";
