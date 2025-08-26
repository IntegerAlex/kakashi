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
    title: 'High Performance',
    imageSrc: require('@site/static/img/socialcard.png').default,
    description: (
      <>
        Kakashi delivers blazing-fast logging performance with minimal overhead,
        designed for production workloads and high-traffic applications.
      </>
    ),
  },
  {
    title: 'Structured Logging',
    imageSrc: require('@site/static/img/socialcard.png').default,
    description: (
      <>
        Built-in support for structured logging with JSON output, making logs
        machine-readable and easier to analyze in modern observability tools.
      </>
    ),
  },
  {
    title: 'Web Framework Integration',
    imageSrc: require('@site/static/img/socialcard.png').default,
    description: (
      <>
        First-class support for FastAPI, Flask, and Django with automatic
        request context capture and performance monitoring.
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
