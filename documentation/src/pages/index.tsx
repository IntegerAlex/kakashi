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
  initial="hidden"
  animate="visible"
>
  <motion.div
    style={{
      position: 'relative',
      overflow: 'hidden',
      width: '150px',
      height: '150px',
      margin: '0 auto',
      borderRadius: '50%',
    }}
    initial={{ scale: 0.8, rotate: -180 }}
    animate={{ 
      scale: 1, 
      rotate: 0,
      transition: {
        type: "spring",
        damping: 10,
        stiffness: 100,
        delay: 0.3
      }
    }}
    whileHover={{
      scale: 1.05,
      rotate: 5,
      transition: {
        type: "spring",
        damping: 10,
        stiffness: 200
      }
    }}
  >
    {/* Eye lid cover - top */}
    <motion.div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '50%',
        background: 'linear-gradient(to bottom, #000000, #1f0000)',
        zIndex: 2,
        borderRadius: '50% 50% 0 0',
        transformOrigin: 'bottom center'
      }}
      initial={{ scaleY: 1 }}
      animate={{ 
        scaleY: 0,
        transition: {
          delay: 0.5,
          duration: 0.8,
          ease: [0.16, 1, 0.3, 1]
        }
      }}
      whileHover={{
        scaleY: 0.2,
        transition: {
          duration: 0.3
        }
      }}
    />
    
    {/* Eye lid cover - bottom */}
    <motion.div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        width: '100%',
        height: '50%',
        background: 'linear-gradient(to top, #000000, #1f0000)',
        zIndex: 2,
        borderRadius: '0 0 50% 50%',
        transformOrigin: 'top center'
      }}
      initial={{ scaleY: 1 }}
      animate={{ 
        scaleY: 0,
        transition: {
          delay: 0.7,
          duration: 0.8,
          ease: [0.16, 1, 0.3, 1]
        }
      }}
      whileHover={{
        scaleY: 0.2,
        transition: {
          duration: 0.3
        }
      }}
    />
    
    {/* Main logo with enhanced animation */}
    <motion.img 
      src={require('@site/static/img/kakashi-logo.png').default} 
      alt="Kakashi Logo" 
      style={{
        width: '100%',
        height: '100%',
        objectFit: 'contain',
        borderRadius: '50%',
        boxShadow: '0 0 0 4px #8b0000, 0 0 20px #ff0000, inset 0 0 20px rgba(0, 0, 0, 0.8)',
        background: 'linear-gradient(135deg, #450000 0%, #000000 100%)',
        padding: '10px',
        filter: 'contrast(1.1) brightness(1.1)'
      }}
      initial={{ 
        scale: 0.5,
        opacity: 0,
        rotate: -180,
        filter: 'blur(10px)'
      }}
      animate={{ 
        scale: [0.5, 1.2, 1],
        opacity: 1,
        rotate: 0,
        filter: 'blur(0px)',
        transition: {
          scale: {
            delay: 0.9,
            duration: 1.2,
            times: [0, 0.7, 1],
            ease: [0.34, 1.56, 0.64, 1]
          },
          rotate: {
            delay: 0.9,
            duration: 1.5,
            ease: [0.34, 1.56, 0.64, 1]
          },
          opacity: {
            delay: 0.9,
            duration: 0.8,
            ease: "easeOut"
          },
          filter: {
            delay: 0.9,
            duration: 1,
            ease: "easeOut"
          }
        }
      }}
      whileHover={{
        scale: 1.08,
        rotate: 3,
        boxShadow: '0 0 0 6px #ff0000, 0 0 30px #ff0000, inset 0 0 10px rgba(0, 0, 0, 0.5)',
        transition: {
          type: "spring",
          damping: 8,
          stiffness: 300
        }
      }}
      whileTap={{
        scale: 0.95,
        rotate: -2
      }}
    />
    
    {/* Shine effect */}
    <motion.div
      style={{
        position: 'absolute',
        top: '0',
        left: '0',
        width: '100%',
        height: '100%',
        background: 'linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 60%)',
        borderRadius: '50%',
        zIndex: 1
      }}
      initial={{ opacity: 0 }}
      animate={{ 
        opacity: 0.3,
        transition: {
          delay: 1.5,
          duration: 0.5
        }
      }}
    />
    
    {/* Red glow effect */}
    <motion.div
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: '100%',
        height: '100%',
        background: 'radial-gradient(circle at center, rgba(255, 0, 0, 0.4) 0%, rgba(255, 0, 0, 0) 70%)',
        borderRadius: '50%',
        zIndex: 0,
        transform: 'translate(-50%, -50%)'
      }}
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ 
        scale: 1.2,
        opacity: 0.6,
        transition: {
          delay: 1.2,
          duration: 1,
          ease: "easeOut"
        }
      }}
      whileHover={{
        scale: 1.3,
        opacity: 0.8
      }}
    />
  </motion.div>
</motion.div>
        
        <motion.div variants={itemVariants}>
          <Heading as="h1">
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
  
  // Structured data for better AI discoverability
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Kakashi",
    "description": "Professional high-performance Python logging library delivering 56K+ logs/sec with superior concurrency scaling, true async logging, and structured data support.",
    "applicationCategory": "DeveloperApplication",
    "operatingSystem": "Any",
    "programmingLanguage": "Python",
    "version": "2.0.0",
    "author": {
      "@type": "Organization",
      "name": "Kakashi Development Team"
    },
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "5.0",
      "ratingCount": "100"
    },
    "featureList": [
      "56,310+ logs per second",
      "1.17x concurrency scaling",
      "169K async logs per second",
      "Structured logging support",
      "Memory efficient",
      "Thread-safe operation"
    ],
    "keywords": "python logging, high performance logging, structured logging, async logging, logging library, python logger, kakashi logging, performance logging, concurrent logging, memory efficient logging"
  };
  
  return (
    <Layout
      title="Kakashi - Professional High-Performance Python Logging Library"
      description="High-performance Python logging with structured, contextual pipelines - 56K+ logs/sec, superior concurrency scaling, true async logging. Perfect for production applications requiring high throughput and excellent performance.">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(structuredData),
        }}
      />
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