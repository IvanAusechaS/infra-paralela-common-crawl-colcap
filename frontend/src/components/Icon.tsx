/**
 * Icon Component - News2Market
 * Reusable SVG icon wrapper
 */

import React from 'react';

interface IconProps {
  name: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Icon map for available icons
const icons: Record<string, React.FC<React.SVGProps<SVGSVGElement>>> = {};

const Icon: React.FC<IconProps> = ({ name, className = '', size = 'md' }) => {
  const sizeClasses = {
    sm: 'icon-sm',
    md: '',
    lg: 'icon-lg',
    xl: 'icon-xl',
  };

  const IconComponent = icons[name];
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }

  return (
    <span className={`icon ${sizeClasses[size]} ${className}`}>
      <IconComponent />
    </span>
  );
};

export default Icon;
