import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  mainSidebar: [
    {
      type: 'category',
      label: 'Overview',
      collapsed: false,
      items: [
        'overview/intro',
        'overview/features',
        'overview/architecture',
      ],
    },
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'getting-started/installation',
        'getting-started/quickstart',
        'getting-started/configuration',
      ],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/structured-logging',
        'guides/context-management',
        'guides/color-configuration',
        'guides/file-rotation',
        'guides/web-integrations',
        'guides/pipeline-composition',
        'guides/async-backends',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/core',
        'api/colors',
        'api/integrations',
      ],
    },
    {
      type: 'category',
      label: 'Operations',
      items: [
        'operations/log-format',
        'operations/log-file-organization',
        'operations/deprecations',
      ],
    },
    {
      type: 'category',
      label: 'Development',
      items: [
        'development/contributing',
        'development/testing',
        'development/performance',
        'development/perf-results',
      ],
    },
  ],
};

export default sidebars;
