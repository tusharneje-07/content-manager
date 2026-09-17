---
version: alpha
name: Tailwind CSS
slug: tailwindcss
source: https://tailwindcss.com/
extractedAt: "2026-05-19"
description: "Dark-first content workspace with a violet-led accent, layered navy surfaces, Manrope typography, JetBrains Mono metadata, refined controls, and responsive utility-class examples."

colors:
  primary: "#00a5ef"
  accent: "#38bdf8"
  accentHover: "#0084cc"
  accentPressed: "#0069a4"
  ink: "#030712"
  body: "#4a5565"
  muted: "#6a7282"
  canvas: "#ffffff"
  surface: "#f9fafb"
  surfaceAlt: "#f3f4f6"
  border: "#e5e7eb"
  borderStrong: "#d1d5dc"
  link: "#0084cc"
  success: "#00bb7f"
  warning: "#f99c00"
  error: "#e40014"
  darkCanvas: "#030712"
  darkSurface: "#101828"
  darkSurfaceAlt: "#1e2939"
  darkBorder: "#ffffff1a"
  darkBody: "#99a1af"
  cyanSoft: "#f0f9ff"
  cyanLine: "#b8e6fe"
  codeBg: "#1e2939"
  codeTokenFunction: "#fb64b6"
  codeTokenString: "#77d4ff"
  codeTokenComment: "#99a1af"
  pinkSignature: "#f6339a"
  indigoSignature: "#625fff"
  violetSignature: "#8d54ff"
  slatePanel: "#020618"
  dottedGrid: "#0307120a"
  on-primary: "#ffffff"
  on-dark: "#ffffff"

typography:
  display:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 72px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.05em"
  hero:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 56px
    fontWeight: 600
    lineHeight: 1.07
    letterSpacing: "-0.05em"
  headline-lg:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 40px
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-0.05em"
  title-lg:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 30px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  title-md:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 20px
    fontWeight: 500
    lineHeight: 1.6
    letterSpacing: "0em"
  title-sm:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "0em"
  body:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.75
    letterSpacing: "0em"
  label:
    fontFamily: "JetBrains Mono, SFMono-Regular, Consolas, monospace"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.85
    letterSpacing: "0.1em"
  button:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.43
    letterSpacing: "0em"
  caption:
    fontFamily: "Manrope, Avenir Next, system-ui, sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.54
    letterSpacing: "0em"
  legal:
    fontFamily: "Inter, Inter Fallback, system-ui, sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.67
    letterSpacing: "0em"
  code:
    fontFamily: "JetBrains Mono, SFMono-Regular, Consolas, monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.75
    letterSpacing: "0em"
  pricing-display:
    fontFamily: "Inter, Inter Fallback, system-ui, sans-serif"
    fontSize: 60px
    fontWeight: 300
    lineHeight: 1
    letterSpacing: "-0.025em"

rounded:
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  "2xl": 16px
  "4xl": 32px
  pill: 9999px

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  "2xl": 64px
  section: 96px

shadows:
  xs: "0 1px 2px 0 #0000000d"
  sm: "0 1px 3px 0 #0000001a, 0 1px 2px -1px #0000001a"
  md: "0 4px 6px -1px #0000001a, 0 2px 4px -2px #0000001a"
  lg: "0 10px 15px -3px #0000001a, 0 4px 6px -4px #0000001a"
  inset-dark-edge: "inset 0 1px #ffffff0d"

components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-dark}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: 8px 16px
  button-primary-active:
    backgroundColor: "{colors.darkSurfaceAlt}"
    textColor: "{colors.on-dark}"
    rounded: "{rounded.pill}"
  button-accent:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: 8px 16px
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: 8px 16px
  button-ghost:
    backgroundColor: transparent
    textColor: "{colors.body}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: 8px 12px
  button-icon:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border}"
    rounded: "{rounded.pill}"
    size: 36px
  nav-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border}"
    height: 64px
  docs-sidebar:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    borderColor: "{colors.border}"
    typography: "{typography.caption}"
  search-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.body}"
    borderColor: "{colors.border}"
    rounded: "{rounded.pill}"
    padding: 8px 12px
  code-panel:
    backgroundColor: "{colors.codeBg}"
    textColor: "{colors.on-dark}"
    typography: "{typography.code}"
    rounded: "{rounded.xl}"
    padding: 24px
  demo-browser-frame:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border}"
    rounded: "{rounded.xl}"
    shadow: "{shadows.lg}"
  feature-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border}"
    rounded: "{rounded.xl}"
    padding: 24px
  grid-section:
    backgroundColor: "{colors.canvas}"
    borderColor: "{colors.border}"
    pattern: "1px hairlines with 10px dotted/radial grid"
  pricing-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border}"
    rounded: "{rounded.2xl}"
    padding: 32px
  pricing-card-dark:
    backgroundColor: "{colors.darkCanvas}"
    textColor: "{colors.on-dark}"
    borderColor: "{colors.darkBorder}"
    rounded: "{rounded.2xl}"
    padding: 32px
  docs-callout:
    backgroundColor: "{colors.cyanSoft}"
    textColor: "{colors.ink}"
    borderColor: "{colors.cyanLine}"
    rounded: "{rounded.xl}"
    padding: 20px
  syntax-token-accent:
    textColor: "{colors.codeTokenFunction}"
    typography: "{typography.code}"
  footer:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    borderColor: "{colors.border}"
---

**Overview**

Tailwind CSS presents itself as a precise, technical, and quietly expressive developer brand. The visual system is built from Tailwind’s own vocabulary: 4px spacing, utility-scale typography, crisp gray borders, cyan action color, rounded pills, code panels, and dense responsive examples. It feels fast and engineered, but not cold; the cyan, pink, indigo, and violet accents give examples and product modules a bright “syntax highlighting” energy.

There are two related modes. The marketing homepage is airy, high-contrast, and demonstration-led, with large tightly tracked headlines, product screenshots, code blocks, hairline grid dividers, and dark preview islands. The docs mode is denser and more utilitarian, with a left sidebar, right table of contents, search, code snippets, and text-first hierarchy. Tailwind Plus adds a commercial gallery mode: polished component thumbnails, pricing cards, and category browsers, still using the same Manrope plus JetBrains Mono foundation.

Key Characteristics:

- Cyan-blue action color anchored by {colors.primary}, supported by pink, indigo, violet, and sky accents.
- Near-black ink on white, with a full dark-mode counterpart using {colors.darkCanvas}.
- Manrope for product and marketing voice; JetBrains Mono for compact metadata, utility names, and technical proof.
- Very tight display tracking, often {typography.display} or {typography.hero}, with balanced headline wrapping.
- Hairline grid systems, 1px rings, dotted 10px textures, and low-opacity borders instead of heavy decoration.
- Rounded pill buttons and search controls contrasted with modest 8-16px cards and code panels.
- Product-specific modules: code panels, utility-class demonstrations, docs sidebars, component galleries, and pricing cards.

**Colors**

Primary & Action:

{colors.primary} is the signature action blue. It appears in links, active docs markers, highlighted borders, DocSearch accents, and product callouts; use it when an element means “continue, learn, install, inspect, or navigate.”

{colors.accent} is the brighter sky highlight. It appears in the logo wave, syntax-like emphasis, and small visual flourishes where the brand needs light without becoming pastel.

{colors.accentHover} and {colors.accentPressed} are the practical interaction depths for links and active states. Prefer these over inventing darker blues, because Tailwind’s brand blue stays clean and cyan rather than royal.

{colors.link} is used for inline navigation and documentation references. It should be legible, sparse, and surrounded by neutral text so it reads as developer affordance instead of marketing decoration.

Surfaces:

{colors.canvas} is the default marketing and docs background. It keeps examples crisp and makes the cyan/pink syntax accents feel intentional.

{colors.surface} and {colors.surfaceAlt} provide subtle panels, search fields, category rows, and muted module backgrounds. They should feel almost white; the system relies on border and spacing more than filled blocks.

{colors.darkCanvas}, {colors.darkSurface}, and {colors.darkSurfaceAlt} support code, previews, dark-mode docs, and selected commercial panels. Dark surfaces should carry white text, faint borders, and selective cyan highlights rather than broad gradients.

Neutrals & Text:

{colors.ink} is Tailwind’s main authority color: headings, primary buttons, nav text, and high-value labels. It is very close to black but slightly blue-gray, preserving the technical feel.

{colors.body} is the long-form reading color. It appears in descriptions, docs prose, component summaries, and pricing explanations.

{colors.muted} handles secondary metadata, footer links, inactive sidebar items, placeholder copy, and supporting captions.

{colors.border} and {colors.borderStrong} are structural tokens. Use them for 1px lines, card rings, table dividers, sidebars, and preview frames.

Semantic:

{colors.success} should be reserved for positive code/demo feedback, inserted diff lines, success badges, and confirmation states.

{colors.warning} fits compatibility notes, migration warnings, and payment/tax information when caution is required.

{colors.error} is for destructive actions, failed validation, and deleted diff tokens. It should not be used decoratively.

Brand-specific signatures:

{colors.codeBg} is the default dark code panel, frequently paired with {typography.code}. It creates the strongest product association because Tailwind sells the code-to-interface loop.

{colors.codeTokenFunction}, {colors.codeTokenString}, and {colors.codeTokenComment} recreate Tailwind’s code-demo chroma. Use them sparingly in code, labels, and product visualizations.

{colors.pinkSignature}, {colors.indigoSignature}, and {colors.violetSignature} are secondary feature accents. They work best as per-card accents, category markers, or syntax-like highlights, not broad page washes.

{colors.dottedGrid} represents the faint technical grid. It should appear as a restrained texture or line system, never as a loud pattern.

**Typography**

Tailwind’s main family is Manrope with a local fallback generated by the site. Code and technical labels use JetBrains Mono; older/source-specific docs assets also expose Source Sans Pro and Ubuntu Mono, but the active brand expression is Manrope plus JetBrains Mono. Manrope’s OpenType features favor UI clarity, while the mono face carries code credibility and small uppercase labels.

| Level | Size | Weight | Line height | Letter spacing |
|---|---:|---:|---:|---:|
| display | 72px | 600 | 1.00 | -0.05em |
| hero | 56px | 600 | 1.07 | -0.05em |
| headline-lg | 40px | 500 | 1.10 | -0.05em |
| title-lg | 30px | 600 | 1.20 | -0.025em |
| title-md | 20px | 500 | 1.60 | 0em |
| title-sm | 16px | 600 | 1.50 | 0em |
| body | 16px | 400 | 1.75 | 0em |
| label | 13px | 500 | 1.85 | 0.1em |
| button | 14px | 600 | 1.43 | 0em |
| caption | 13px | 400 | 1.54 | 0em |
| legal | 12px | 400 | 1.67 | 0em |
| code | 13px | 400 | 1.75 | 0em |
| pricing-display | 60px | 300 | 1.00 | -0.025em |

Principles:

- Track large display type tightly; {typography.display} and {typography.hero} should feel compact and confident.
- Keep body copy relaxed at {typography.body}, especially in docs and feature descriptions.
- Use mono typography for proof, not personality alone: command lines, class names, version labels, code captions, and eyebrow labels.
- Prefer medium and semibold weights over heavy black type. Tailwind’s voice is exact, not shouty.
- Preserve tabular clarity in pricing and code by pairing large numerals with quiet explanatory labels.

**Layout**

Tailwind’s layout rhythm is based on a 4px spacing unit. Common clusters use 8px, 16px, 24px, 40px, 64px, and section-scale 96px or more. Content typically sits in centered containers up to 80rem, with docs using a three-column structure: sidebar navigation, main prose/code column, and right-side table of contents.

| Token | Value | Use |
|---|---:|---|
| {spacing.xs} | 4px | Icon gaps, tiny offsets, ring spacing |
| {spacing.sm} | 8px | Button padding, compact stacks |
| {spacing.md} | 16px | Form fields, nav groups, card internals |
| {spacing.lg} | 24px | Code panels, card padding, grid gutters |
| {spacing.xl} | 40px | Feature blocks, heading-to-content gaps |
| {spacing.2xl} | 64px | Major bands, hero modules |
| {spacing.section} | 96px | Marketing sections and large docs separations |

Whitespace is purposeful and grid-bound. Marketing pages give large headlines room, then quickly anchor them with concrete demos. Docs pages use less open space and more vertical rhythm; the page should feel scannable, not editorially loose.

**Elevation & Depth**

Tailwind rarely depends on dramatic shadows. Depth usually comes from 1px rings, low-opacity borders, nested surfaces, dark code panels, and line-based grids. When a shadow is used, {shadows.lg} is modest: `0 10px 15px -3px #0000001a, 0 4px 6px -4px #0000001a`.

Use elevation to separate live previews, pricing cards, and floating search/dialog layers. For normal feature cards and docs modules, prefer {colors.border}, {colors.surface}, and clear spacing. Dark panels may use inset highlights like `inset 0 1px #ffffff0d` to create a crisp top edge.

**Components**

Buttons:

{components.button-primary} is usually a black pill with white text. It carries primary marketing actions and should feel compact, not oversized; use the cyan button only when the surrounding page already has enough black anchors.

{components.button-accent} uses {colors.primary} for high-energy actions such as install, start, or focused docs movement. Pair it with white text and keep the same pill geometry.

{components.button-secondary} is a white or near-white pill with a fine border. It works beside primary CTAs, for “Documentation,” “Browse UI blocks,” and lower-commitment actions.

{components.button-ghost} is text-first navigation. It should rely on color and hover background instead of visible chrome.

{components.button-icon} is circular or pill-like, 36px, and quietly bordered. Use it for theme toggles, menu triggers, search icons, and social links.

Cards & Containers:

{components.feature-card} is a restrained bordered card, usually with a small visual demo, a compact heading, and body copy. The card should not look like a marketing tile from a generic SaaS template; it needs code, utility names, or product proof.

{components.code-panel} is one of the most important signature elements. It uses dark slate, JetBrains Mono, 13px code, and syntax colors that map to {colors.codeTokenFunction}, {colors.codeTokenString}, and {colors.codeTokenComment}.

{components.demo-browser-frame} frames visual output generated by code. Use it for product examples where Tailwind wants to show code and UI in direct conversation.

{components.grid-section} creates a technical skeleton with hairline separators, dotted 10px textures, and precise columns. It should stay quiet enough that content remains the hero.

Inputs & Forms:

{components.search-input} is rounded, compact, and neutral. In docs it acts as both navigation and command surface; include icon affordances and keyboard hints where appropriate.

Forms should use Inter, 1px borders, 8-12px vertical padding, and focus treatments based on {colors.primary}. Avoid chunky filled fields unless inside a dark preview.

Navigation:

{components.nav-shell} is slim, centered, and content-dense. Logo, links, version/product links, search, and theme controls fit into a 64px rhythm with minimal decoration.

{components.docs-sidebar} is the utility navigation pattern. It uses muted text, active cyan or ink states, sticky positioning, and tight vertical lists.

{components.footer} is quiet and link-heavy. It should look like documentation infrastructure rather than a promotional closer.

Pricing:

{components.pricing-card} is a clear commercial container with strong plan title, light explanatory copy, and a large {typography.pricing-display} price. It uses generous internal spacing but remains rectangular and efficient.

{components.pricing-card-dark} is the emphasized plan or dark Plus module. It uses near-black canvas, white type, subtle borders, and cyan/pink accents rather than large decorative gradients.

Signature Components:

{components.docs-callout} is a restrained educational note. Use it for compatibility, installation, and migration guidance with a cyan left edge or border.

{components.syntax-token-accent} is the smallest but most brand-specific detail: code colors become visual identity. Use these accents in code snippets and class-name demos before adding any illustration.

**Do's and Don'ts**

Do:

- Use {colors.primary} for active links, selected docs anchors, and focused UI states.
- Pair {typography.display} with balanced wrapping and short, concrete product claims.
- Build examples around {components.code-panel} plus {components.demo-browser-frame} whenever explaining product value.
- Use 1px {colors.border} or {colors.darkBorder} lines to organize dense content.
- Keep CTAs pill-shaped with {rounded.pill} and {typography.button}.
- Use {typography.label} for uppercase-ish technical labels, version tags, and utility names.
- Let {colors.pinkSignature}, {colors.indigoSignature}, and {colors.violetSignature} mark categories or syntax accents.

Don't:

- Do not replace Tailwind cyan with generic royal blue or purple gradients.
- Do not use heavy drop shadows on normal feature cards; use rings and borders first.
- Do not round every surface into soft blobs; reserve {rounded.pill} for buttons/search and use {rounded.xl} for panels.
- Do not set large headings with normal tracking; display type needs the tight Tailwind feel.
- Do not make documentation pages sparse like landing pages; docs should be navigable and information-dense.
- Do not use decorative illustrations where a code/demo pair would communicate the brand better.
- Do not overuse dark panels; dark mode should punctuate code and previews, not swallow every page.

**Responsive Behavior**

| Breakpoint | Width | Behavior |
|---|---:|---|
| sm | 40rem / 640px | Mobile-to-tablet layout begins; stacks tighten |
| md | 48rem / 768px | Two-column cards and richer nav options appear |
| lg | 64rem / 1024px | Docs sidebars and multi-column demos stabilize |
| xl | 80rem / 1280px | Full marketing grids and wide previews are comfortable |
| 2xl | 96rem / 1536px | Max-width containers preserve readable line length |

Touch targets should stay at least 36px visually and 44px interactively, especially icon buttons and mobile nav triggers. Small text may remain 13-14px only when surrounded by enough hit area.

Collapsing strategy:

- Collapse docs sidebars into mobile navigation while keeping search prominent.
- Stack code and preview modules vertically before shrinking code below readable width.
- Preserve pill CTAs on mobile, but let pairs wrap to two lines if needed.
- Hide secondary nav links before reducing logo/search recognition.
- Keep grids as structural lines; reduce columns, not spacing consistency.

Images and previews should scale fluidly with fixed aspect ratios. Product screenshots should remain sharp and inspectable; avoid cropping away the actual code or UI being demonstrated.

**Iteration Guide**

1. Check that the first screen uses {colors.ink}, {colors.primary}, and white/near-white surfaces before any extra accent colors.
2. Verify display headings use {typography.display} or {typography.hero} with tight negative tracking.
3. Inspect every CTA: primary actions should match {components.button-primary} or {components.button-accent}, with pill geometry.
4. Confirm at least one product proof module uses {components.code-panel}, class-name text, syntax accents, or a demo frame.
5. Audit borders: cards, nav, docs rails, and previews should use 1px lines from {colors.border} or {colors.darkBorder}.
6. Compare docs screens against {components.docs-sidebar}; navigation should be dense, sticky, and muted until active.
7. Test dark surfaces for restraint: use {colors.darkCanvas} and subtle inset/ring details, not heavy gradients.
8. Review responsive layouts by stacking code/preview pairs before reducing type below readable sizes.

**Known Gaps**

Observed directly: homepage, Tailwind Plus/pricing content, component gallery, docs installation page, linked CSS variables, font-face declarations, color variables, type utilities, radius tokens, spacing tokens, shadows, docs search styling, and code syntax colors.

Derived: exact component abstractions such as {components.feature-card}, {components.grid-section}, and {components.demo-browser-frame} are synthesized from repeated source patterns rather than named exports. Some hex values are taken from Tailwind’s generated v4 CSS variables; Plus CSS exposes several colors as OKLCH, so the closest Tailwind hex equivalents are used for DESIGN.md portability.

Uncertain: individual hover states and animation timing were inferred from common site utilities and generated CSS, not exhaustively interacted with in a browser. Tailwind Plus commercial pages may vary across templates, so pricing and gallery guidance captures the Tailwind-owned shell rather than every purchasable component style.
