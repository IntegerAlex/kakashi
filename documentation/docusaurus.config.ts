import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Kakashi - Professional High-Performance Python Logging Library',
  tagline: 'High-performance Python logging with structured, contextual pipelines - 56K+ logs/sec, superior concurrency scaling, true async logging',
  favicon: 'img/kakashi-logo.png',

  future: {
    v4: true, 
  },

  url: 'https://docs.kakashi.gossorg.in',
  baseUrl: '/',

  organizationName: 'IntegerAlex', 
  projectName: 'kakashi', 

  // SEO and metadata
  customFields: {
    keywords: 'python logging, high performance logging, structured logging, async logging, logging library, python logger, kakashi logging, performance logging, concurrent logging, memory efficient logging',
    description: 'Kakashi is a professional high-performance Python logging library delivering 56K+ logs/sec with superior concurrency scaling, true async logging, and structured data support. Perfect for production applications requiring high throughput and excellent performance.',
    author: 'Kakashi Development Team',
  },

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

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
          routeBasePath: '/docs',
          editUrl: 'https://github.com/IntegerAlex/kakashi/tree/main/documentation',
        },
        blog: {
          showReadingTime: true,
          postsPerPage: 10,
          blogSidebarTitle: 'All posts',
          blogSidebarCount: 'ALL',
          editUrl: 'https://github.com/IntegerAlex/kakashi/tree/main/documentation',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    
    // SEO and metadata
    metadata: [
      {name: 'keywords', content: 'python logging, high performance logging, structured logging, async logging, logging library, python logger, kakashi logging, performance logging, concurrent logging, memory efficient logging'},
      {name: 'description', content: 'Kakashi is a professional high-performance Python logging library delivering 56K+ logs/sec with superior concurrency scaling, true async logging, and structured data support. Perfect for production applications requiring high throughput and excellent performance.'},
      {name: 'author', content: 'Kakashi Development Team'},
      {name: 'robots', content: 'index, follow'},
      {name: 'googlebot', content: 'index, follow'},
      {name: 'msapplication-TileColor', content: '#2b5797'},
      {name: 'theme-color', content: '#2b5797'},
      // Open Graph
      {property: 'og:type', content: 'website'},
      {property: 'og:title', content: 'Kakashi - Professional High-Performance Python Logging Library'},
      {property: 'og:description', content: 'High-performance Python logging with structured, contextual pipelines - 56K+ logs/sec, superior concurrency scaling, true async logging'},
      {property: 'og:image', content: 'img/socialcard.png'},
      {property: 'og:url', content: 'https://docs.kakashi.gossorg.in'},
      {property: 'og:site_name', content: 'Kakashi Documentation'},
      // Twitter Card
      {name: 'twitter:card', content: 'summary_large_image'},
      {name: 'twitter:title', content: 'Kakashi - Professional High-Performance Python Logging Library'},
      {name: 'twitter:description', content: 'High-performance Python logging with structured, contextual pipelines - 56K+ logs/sec, superior concurrency scaling, true async logging'},
      {name: 'twitter:image', content: 'img/socialcard.png'},
      // Additional SEO
      {name: 'application-name', content: 'Kakashi'},
      {name: 'apple-mobile-web-app-title', content: 'Kakashi'},
      {name: 'apple-mobile-web-app-capable', content: 'yes'},
      {name: 'apple-mobile-web-app-status-bar-style', content: 'default'},
    ],
    
    image: 'img/socialcard.png',
    navbar: {
      title: 'Kakashi',
      logo: {
        alt: 'Kakashi Logo',
        src: 'img/kakashi-logo.png',
      },
      items: [
        { type: 'docSidebar', sidebarId: 'mainSidebar', position: 'left', label: 'Docs' },
        { to: '/blog', label: 'Blog', position: 'left' },
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
            { label: 'Blog', to: '/blog' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Kakashi. All rights reserved.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
