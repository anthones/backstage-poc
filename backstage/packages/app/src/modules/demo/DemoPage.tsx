import { Navigate } from 'react-router-dom';

// The owning domain's TechDocs is the only authored engineering handbook.
export function DemoPage() {
  return (
    <Navigate
      replace
      to="/docs/default/component/onboarding-service/handbook"
    />
  );
}
