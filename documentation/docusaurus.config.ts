import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Kakashi',
  tagline: 'High-performance Python logging with structured, contextual pipelines',
  favicon: 'img/kakashi-logo.png',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://kakashi-docs.example.com',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'IntegerAlex', // Usually your GitHub org/user name.
  projectName: 'kakashi', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Route docs at /docs (default)
          routeBasePath: '/docs',
          // Edit URL points to repository documentation directory
          editUrl: 'https://github.com/IntegerAlex/kakashi/tree/main/documentation',
        },
        // Disable blog by default; can be re-enabled and curated later
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Force dark theme only
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    
    // Replace with your project's social card
    image: 'img/socialcard.png',
    navbar: {
      title: 'Kakashi',
      logo: {
        alt: 'Kakashi Logo',
        src: 'img/kakashi-logo.png',
      },
      items: [
        { type: 'docSidebar', sidebarId: 'mainSidebar', position: 'left', label: 'Docs' },
        { href: 'https://pypi.org/project/kakashi/', label: 'PyPI', position: 'right' },
        { href: 'https://github.com/IntegerAlex/kakashi', label: 'GitHub', position: 'right' },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Overview', to: '/docs/overview/intro' },
            { label: 'Getting Started', to: '/docs/getting-started/installation' },
          ],
        },
        {
          title: 'Community',
          items: [
            { label: 'Issues', href: 'https://github.com/IntegerAlex/kakashi/issues' },
          ],
        },
        {
          title: 'More',
          items: [
            { label: 'Repository', href: 'https://github.com/IntegerAlex/kakashi' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Kakashi. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
