export interface ClassData {
  classID: string;
  sectionNumber: string;
  numStudents: string;
  classTitle: string;
}

export interface ApiResponse {
  statusCode: number;
  body: string;
}

export interface ChatHistoryItem {
  TeacherId: string;
  sortId: string;
  created_at: number;
  conversation_id: string;
  title: string;
  type?: string;
  student_ids?: string[];
}

export interface ChatMessageItem {
  TeacherId: string;
  sortId: string;
  created_at: number;
  message: string;
  sender: string;
}

export async function getClassesForDashboard(teacherEmail: string): Promise<ClassData[]> {
  const response = await fetch('/api/classes', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      teacherID: teacherEmail
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch classes: ${response.status}`);
  }

  const data: ApiResponse = await response.json();
  
  if (data.statusCode !== 200) {
    throw new Error('API returned error status');
  }

  return JSON.parse(data.body);
}

export async function getStudentsByClassId(classId: string): Promise<Record<string, string>> {
  const response = await fetch('/api/students', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      classID: classId
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch students: ${response.status}`);
  }

  const data = await response.json();
  
  if (data.statusCode !== 200) {
    throw new Error('API returned error status');
  }

  return typeof data.body === 'string' ? JSON.parse(data.body) : data.body;
}

export async function getStudentProfile(studentId: string): Promise<any> {
  const response = await fetch('/api/student-profile', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      studentID: studentId
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch student profile: ${response.status}`);
  }

  const data = await response.json();
  
  if (data.statusCode !== 200) {
    throw new Error('API returned error status');
  }

  return typeof data.body === 'string' ? JSON.parse(data.body) : data.body;
}

export async function getChatHistory(teacherId: string, classId?: string): Promise<ChatHistoryItem[]> {
  const response = await fetch('/api/chat-history', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      teacherId,
      classId
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch chat history: ${response.status}`);
  }

  const data = await response.json();
  
  if (data.statusCode !== 200) {
    throw new Error('API returned error status');
  }

  return typeof data.body === 'string' ? JSON.parse(data.body) : data.body;
}

export async function getChatMessages(teacherId: string, conversationId: string): Promise<ChatMessageItem[]> {
  const response = await fetch('/api/chat-history', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      teacherId,
      conversationId
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch chat messages: ${response.status}`);
  }

  const data = await response.json();
  
  if (data.statusCode !== 200) {
    throw new Error('API returned error status');
  }

  return typeof data.body === 'string' ? JSON.parse(data.body) : data.body;
}