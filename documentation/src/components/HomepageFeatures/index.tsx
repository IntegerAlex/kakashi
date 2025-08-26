import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  imageSrc: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: '🚀 Superior Performance',
    imageSrc: require('@site/static/img/socialcard.png').default,
    description: (
      <>
        Kakashi achieves <strong>56,310+ logs/sec</strong> with <strong>1.17x concurrency scaling</strong>.
        Thread-local buffering and lock-free hot paths deliver industry-leading performance.
      </>
    ),
  },
  {
    title: '⚡ True Async Logging',
    imageSrc: require('@site/static/img/socialcard.png').default,
    description: (
      <>
        Background worker threads deliver <strong>169,074 logs/sec</strong> with intelligent batch processing.
        Non-blocking operation for maximum throughput applications.
      </>
    ),
  },
  {
    title: '🏗️ Professional Architecture',
    imageSrc: require('@site/static/img/socialcard.png').default,
    description: (
      <>
        Clean, maintainable code with thread-local buffering and efficient memory management.
        Production-ready design with <strong>&lt;0.02MB</strong> memory usage.
      </>
    ),
  },
];

function Feature({title, imageSrc, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img src={imageSrc} className={styles.featureSvg} alt={title} />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
