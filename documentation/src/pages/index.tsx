import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <div className="text--center">
          <img 
            src={require('@site/static/img/kakashi-logo.png').default} 
            alt="Kakashi Logo" 
            className={styles.heroLogo}
          />
        </div>
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className="hero__performance">
          <div className="performance-metric">
            <span className="metric-value">56,310+</span>
            <span className="metric-label">logs/sec</span>
          </div>
          <div className="performance-metric">
            <span className="metric-value">1.17x</span>
            <span className="metric-label">concurrency</span>
          </div>
          <div className="performance-metric">
            <span className="metric-value">169K</span>
            <span className="metric-label">async logs/sec</span>
          </div>
        </div>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/overview/intro">
            Get Started with Kakashi 🚀
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`Hello from ${siteConfig.title}`}
      description="Description will go into a meta tag in <head />">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
