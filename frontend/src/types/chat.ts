export interface ChatMessage {
  id: number;
  sender: string;
  message: string;
  time: string;
  isTeacher: boolean;
}

export interface ChatHistory {
  id: number;
  title: string;
  lastMessage: string;
  time: string;
  type: 'general' | 'student';
  studentId?: number;
  conversationId?: string;
}

export interface Student {
  id: number;
  name: string;
}

export interface ClassInfo {
  title: string;
  section: number;
  color: string;
}