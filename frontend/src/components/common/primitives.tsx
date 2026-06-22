import type { ButtonHTMLAttributes, ReactNode } from 'react';

type SwitchProps = {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
};

import { Switch as RadixSwitch } from '../ui/switch';
export function Switch({ checked, onCheckedChange, label, disabled = false }: SwitchProps) {
  return (
    <RadixSwitch
      checked={checked}
      onCheckedChange={onCheckedChange}
      aria-label={label}
      disabled={disabled}
    />
  );
}

type SegmentedOption<T extends string> = {
  value: T;
  label: string;
};

type SegmentedControlProps<T extends string> = {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
};

export function SegmentedControl<T extends string>({ options, value, onChange }: SegmentedControlProps<T>) {
  const selectedIndex = Math.max(0, options.findIndex((option) => option.value === value));
  return (
    <div className="relative grid rounded-md bg-[#F1F3F5] p-0.5" style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}>
      <span
        className="absolute bottom-0.5 top-0.5 rounded bg-white shadow-lo-elevation-100 transition-transform"
        style={{ left: 2, width: `calc((100% - 4px) / ${options.length})`, transform: `translateX(${selectedIndex * 100}%)` }}
      />
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={`relative z-10 h-7 px-2 text-xs ${option.value === value ? 'text-[#2F3640]' : 'text-[#4A535F]'}`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

type CheckboxProps = {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  label?: ReactNode;
};

export function Checkbox({ checked, onCheckedChange, label }: CheckboxProps) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      onClick={() => onCheckedChange(!checked)}
      className="inline-flex items-center gap-2 text-xs text-[#2F3640]"
    >
      <span className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${checked ? 'border-[#2F3640] bg-[#2F3640]' : 'border-[#D4D7DC] bg-white'}`}>
        {checked ? <span className="h-1.5 w-2.5 rotate-[-45deg] border-b-2 border-l-2 border-white" /> : null}
      </span>
      {label ? <span>{label}</span> : null}
    </button>
  );
}

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  children: ReactNode;
};

export function IconButton({ label, children, className = '', ...props }: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={`inline-flex h-8 w-8 items-center justify-center rounded-md border border-black/10 bg-white text-[#2F3640] shadow-lo-elevation-100 transition-colors hover:bg-[#F1F3F5] ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
