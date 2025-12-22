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

const Icon: React.FC<IconProps> = ({ name, className = '', size = 'md' }) => {
  const sizeClasses = {
    sm: 'icon-sm',
    md: '',
    lg: 'icon-lg',
    xl: 'icon-xl',
  };

  let IconComponent;
  try {
    IconComponent = require(`../assets/icons/${name}.svg?react`).default;
  } catch (error) {
    console.error(`Icon "${name}" not found`);
    return null;
  }

  return (
    <span className={`icon ${sizeClasses[size]} ${className}`}>
      <IconComponent />
    </span>
  );
};

export default Icon;
