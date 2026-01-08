export interface User {
  _id: string;
  id?: string; // Sometimes returned as id in profile
  name: string;
  email: string;
  imageUrl?: string | null;
  currency: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface Group {
  _id: string;
  name: string;
  currency: string;
  joinCode: string;
  createdBy: string;
  createdAt: string;
  imageUrl?: string;
  members?: GroupMember[];
}

export interface GroupMember {
  userId: string;
  role: 'admin' | 'member';
  joinedAt: string;
  user?: User; // Details populated
}

export enum SplitType {
  EQUAL = 'equal',
  UNEQUAL = 'unequal',
  PERCENTAGE = 'percentage'
}

export interface ExpenseSplit {
  userId: string;
  amount: number;
  type?: SplitType;
}

export interface Expense {
  _id: string;
  groupId: string;
  description: string;
  amount: number;
  paidBy: string;
  splitType: SplitType;
  splits: ExpenseSplit[];
  createdAt: string;
  tags?: string[];
}

export interface Settlement {
  _id: string;
  groupId: string;
  payerId: string;
  payeeId: string;
  payerName: string;
  payeeName: string;
  amount: number;
  status: 'pending' | 'completed' | 'cancelled';
  description?: string;
}

export interface GroupBalanceSummary {
  groupId: string;
  groupName: string;
  amount: number; // Positive = owed to you, Negative = you owe
}

export interface BalanceSummary {
  totalOwedToYou: number;
  totalYouOwe: number;
  netBalance: number;
  currency: string;
  groupsSummary: GroupBalanceSummary[];
}

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}
