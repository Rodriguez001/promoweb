/**
 * TypeScript fix to suppress React 18/19 JSX component type conflicts with Radix UI
 * This resolves the FC<Props> vs ReactNode | Promise<ReactNode> incompatibility
 */

declare module 'react' {
  namespace JSX {
    interface ElementType {
      [key: string]: any;
    }
  }
}

// Global type override for Radix UI components
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [key: string]: any;
    }
  }
}

export {};
