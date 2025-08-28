import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';
import {motion, Variants} from 'framer-motion'

import styles from './index.module.css';

// Animation variants for staggered children
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      delayChildren: 0.3,
      staggerChildren: 0.2
    }
  }
};

const itemVariants : Variants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      damping: 12,
      stiffness: 100
    }
  }
};

const logoVariants :  Variants = {
  hidden: { 
    scale: 0.8,
    rotate: -15,
    opacity: 0 
  },
  visible: {
    scale: 1,
    rotate: 0,
    opacity: 1,
    transition: {
      type: "spring",
      damping: 10,
      stiffness: 100,
      delay: 0.2
    }
  },
  hover: {
    scale: 1.05,
    rotate: 5,
    transition: {
      type: "spring",
      damping: 10,
      stiffness: 200
    }
  }
};

const metricVariants : Variants = {
  hidden: { scale: 0.9, opacity: 0 },
  visible: (i: number) => ({
    scale: 1,
    opacity: 1,
    transition: {
      delay: i * 0.1 + 0.8,
      type: "spring",
      damping: 10,
      stiffness: 100
    }
  }),
  hover: {
    scale: 1.05,
    y: -5,
    transition: {
      type: "spring",
      damping: 10,
      stiffness: 300
    }
  }
};

const buttonVariants : Variants = {
  hidden: { scale: 0.9, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      delay: 1.2,
      type: "spring",
      damping: 10,
      stiffness: 100
    }
  },
  hover: {
    scale: 1.05,
    boxShadow: "0px 5px 15px rgba(0, 0, 0, 0.2)",
    transition: {
      type: "spring",
      damping: 10,
      stiffness: 300
    }
  },
  tap: {
    scale: 0.95
  }
};

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  
  return (
    <motion.header 
      className={clsx('hero hero--primary', styles.heroBanner)}
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <div className="container">
        <motion.div 
          className="text--center"
          variants={itemVariants}
        >
          <motion.img 
            src={require('@site/static/img/kakashi-logo.png').default} 
            alt="Kakashi Logo" 
            className={styles.heroLogo}
            variants={logoVariants}
            initial="hidden"
            animate="visible"
            whileHover="hover"
          />
        </motion.div>
        
        <motion.div variants={itemVariants}>
          <Heading as="h1" className="hero__title">
            {siteConfig.title}
          </Heading>
        </motion.div>
        
        <motion.div variants={itemVariants}>
          <p className="hero__subtitle">{siteConfig.tagline}</p>
        </motion.div>
        
        <motion.div 
          className="hero__performance"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div 
            className="performance-metric"
            variants={metricVariants}
            custom={0}
            whileHover="hover"
          >
            <span className="metric-value">56,310+</span>
            <span className="metric-label">logs/sec</span>
          </motion.div>
          
          <motion.div 
            className="performance-metric"
            variants={metricVariants}
            custom={1}
            whileHover="hover"
          >
            <span className="metric-value">1.17x</span>
            <span className="metric-label">concurrency</span>
          </motion.div>
          
          <motion.div 
            className="performance-metric"
            variants={metricVariants}
            custom={2}
            whileHover="hover"
          >
            <span className="metric-value">169K</span>
            <span className="metric-label">async logs/sec</span>
          </motion.div>
        </motion.div>
        
        <motion.div 
          className={styles.buttons}
          variants={itemVariants}
        >
          <motion.div
            variants={buttonVariants}
            whileHover="hover"
            whileTap="tap"
          >
            <Link
              className="button button--secondary button--lg"
              to="/docs/overview/intro"
            >
              Get Started with Kakashi 🚀
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </motion.header>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  
  return (
    <Layout
      title={`Hello from ${siteConfig.title}`}
      description="Description will go into a meta tag in <head />">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <HomepageHeader />
      </motion.div>
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}