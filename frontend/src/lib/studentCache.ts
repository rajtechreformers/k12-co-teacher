// Student roster cache for class-specific data
class StudentCache {
  private cache: Map<string, Record<string, string>> = new Map();

  set(classId: string, students: Record<string, string>) {
    this.cache.set(classId, students);
  }

  get(classId: string): Record<string, string> | null {
    return this.cache.get(classId) || null;
  }

  clear(classId?: string) {
    if (classId) {
      this.cache.delete(classId);
    } else {
      this.cache.clear();
    }
  }

  has(classId: string): boolean {
    return this.cache.has(classId);
  }
}

export const studentCache = new StudentCache();