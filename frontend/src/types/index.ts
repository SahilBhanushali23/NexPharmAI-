// NexPharmAI Core Data Contracts

export type UserRole = 
  | 'ADMIN'
  | 'PRODUCTION_MANAGER'
  | 'MAINTENANCE_MANAGER'
  | 'QUALITY_MANAGER'
  | 'OPERATOR';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export type MachineStatus = 
  | 'RUNNING'
  | 'IDLE'
  | 'WARNING'
  | 'CRITICAL'
  | 'MAINTENANCE'
  | 'OFFLINE';

export interface Machine {
  id: string;
  machine_id: string;
  machine_name: string;
  machine_type: 'L' | 'M' | 'H' | string;
  production_line: string;
  location: string;
  status: MachineStatus;
  installation_date?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  created_at: string;
  updated_at: string;
}

export interface MachineReading {
  id: string;
  machine_id: string;
  timestamp: string;
  air_temperature: number;
  process_temperature: number;
  rotational_speed: number;
  torque: number;
  tool_wear: number;
}

export interface MachineHealth {
  machine_id: string;
  score: number; // 0-100
  category: 'EXCELLENT' | 'GOOD' | 'WARNING' | 'CRITICAL';
  failure_probability: number;
  anomaly_score: number;
  anomaly_severity: 'NORMAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  timestamp: string;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface ApiError {
  message: string;
  status_code?: number;
  details?: unknown;
}
