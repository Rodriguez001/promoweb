// Global TypeScript declarations for PromoWeb Africa

declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }

  interface Window {
    // Service Worker
    workbox: any;
    
    // Analytics
    gtag: (command: string, targetId: string, config?: any) => void;
    
    // Payment gateways
    Stripe: any;
    
    // PWA
    deferredPrompt: any;
  }

  // Environment variables
  namespace NodeJS {
    interface ProcessEnv {
      NODE_ENV: 'development' | 'production' | 'test';
      NEXT_PUBLIC_API_URL: string;
      NEXT_PUBLIC_APP_URL: string;
      NEXTAUTH_URL: string;
      NEXTAUTH_SECRET: string;
      NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: string;
      NEXT_PUBLIC_GA_TRACKING_ID: string;
      NEXT_PUBLIC_SENTRY_DSN: string;
      NEXT_PUBLIC_ENABLE_PWA: string;
      NEXT_PUBLIC_ENABLE_ANALYTICS: string;
    }
  }
}

// Module augmentations
declare module '*.svg' {
  const content: React.FunctionComponent<React.SVGAttributes<SVGElement>>;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.webp' {
  const content: string;
  export default content;
}

declare module '*.ico' {
  const content: string;
  export default content;
}

declare module '*.woff' {
  const content: string;
  export default content;
}

declare module '*.woff2' {
  const content: string;
  export default content;
}

export {};
